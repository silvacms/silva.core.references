# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from AccessControl import ClassSecurityInfo
from Acquisition import aq_parent
from App.class_init import InitializeClass
from zExceptions import BadRequest

from dolmen.relations.events import IRelationTargetDeletedEvent
from dolmen.relations.events import RelationModifiedEvent
from dolmen.relations.values import TaggedRelationValue
from five import grok
from zope import schema
from zope.component import getUtility
from zope.event import notify
from zope.intid.interfaces import IIntIds

from silva.core.interfaces import IContainerManager
from silva.core.interfaces import IReferable
from silva.core.services.delayed import Task

from .utils import is_inside_container
from .utils import relative_path
from .interfaces import IReferenceValue
from .interfaces import IWeakReferenceValue, IDeleteSourceReferenceValue
from .interfaces import IReference, IReferenceService


class ResolverTask(Task):

    def __init__(self):
        service = getUtility(IIntIds)
        self._get_identifier = service.register
        self._get_content = service.getObject

    def get_content_id(self, content):
        if content is None:
            return 0
        return self._get_identifier(content)

    def get_content_from_id(self, content_id):
        if content_id == 0:
            return None
        try:
            return self._get_content(content_id)
        except KeyError:
            return None

    def copy(self):
        return ResolverTask()


def get_content_id(content):
    """Return the ID of a content.
    """
    return ResolverTask.get().get_content_id(content)


def get_content_from_id(content_id):
    """Return a content from its ID.
    """
    return ResolverTask.get().get_content_from_id(content_id)


class Reference(schema.Object):
    """Store a reference to an object.
    """
    grok.implements(IReference)

    missing_value = None
    multiple = False

    def __init__(self, schema, **kw):
        if 'multiple' in kw:
            self.multiple = kw['multiple']
            del kw['multiple']
        super(Reference, self).__init__(schema, **kw)

    def _validate(self, value):
        # XXX No validation for the moment
        pass


class ReferenceValue(TaggedRelationValue):
    """Store a reference information.
    """
    grok.implements(IReferenceValue)

    security = ClassSecurityInfo()
    security.declareProtected('View', 'target')
    security.declareProtected('View', 'source')

    def add_tag(self, name):
        assert isinstance(name, unicode), 'The tag must be a unicode string'
        self.tags.append(name)
        notify(RelationModifiedEvent(self))

    def set_target_id(self, target_id):
        self.target_id = target_id
        notify(RelationModifiedEvent(self))

    def set_target(self, target):
        self.set_target_id(get_content_id(target))

    def set_source_id(self, source_id):
        self.source_id = source_id
        notify(RelationModifiedEvent(self))

    def set_source(self, source):
        self.set_source_id(get_content_id(source))

    def is_target_inside_container(self, container):
        return is_inside_container(container, self.target)

    def is_source_inside_container(self, container):
        return is_inside_container(container, self.source)

    def relative_path_to(self, content):
        target = self.target
        if target is None:
            # The reference is broken
            return []
        return relative_path(
            content.getPhysicalPath(),
            target.getPhysicalPath())

    def cleanup(self):
        """This method is called when the reference is removed. In any
        case, you should not consider to call this yourself.
        """
        if self.source is not None:
            # Source is not gone
            raise BrokenReferenceError(self)


InitializeClass(ReferenceValue)


class WeakReferenceValue(ReferenceValue):
    """ This reference type do not enforce the relation to be kept.
    """
    grok.implements(IWeakReferenceValue)

    def cleanup(self):
        # We do nothing when cleaning this reference.
        pass


class DeleteSourceReferenceValue(ReferenceValue):
    """ This reference delete its source when the target is removed.
    """
    grok.implements(IDeleteSourceReferenceValue)

    def cleanup(self):
        source = self.source    # Cache the property
        if source is not None:
            source = source.get_silva_object()
            parent = aq_parent(source)
            with IContainerManager(parent).deleter() as deleter:
                deleter(source)


class ReferenceSet(object):
    """ A helper to manage multiple references relationship between a
    unique source and several objects.
    """
    # XXX The name of this class is misleading and should be changed

    def __init__(self, source, name, factory=WeakReferenceValue):
        self._source = source
        self._factory = factory
        self._name = unicode(name)
        self._service = getUtility(IReferenceService)

    def get_references(self):
        return self._service.get_references_from(
            self._source, name=self._name)

    def get(self):
        return list(self)

    def set(self, items):
        # Collect existing references
        name_to_target = {}
        target_to_name = {}
        for reference in self.get_references():
            name_to_target[reference.__name__] = reference.target_id
            target_to_name[reference.target_id] = reference.__name__

        # Add or mark seen set references
        for item in items:
            if not isinstance(item, int):
                item = get_content_id(item)
            if item not in target_to_name:
                # Add item
                reference = self._service.new_reference(
                    self._source, name=self._name, factory=self._factory)
                reference.set_target_id(item)
            else:
                # Remove item from name_to_target
                name = target_to_name[item]
                del target_to_name[item]
                del name_to_target[name]

        # Remove references we didn't see
        for name in name_to_target.keys():
            self._service.delete_reference_by_name(name)

    def add(self, item):
        references = self._service.get_references_between(
            self._source, item, name=self._name)
        try:
            reference = references.next()
        except StopIteration:
            reference = self._service.new_reference(
                self._source, name=self._name, factory=self._factory)
            reference.set_target(item)
        return reference

    def remove(self, item):
        refs = list(self._service.get_references_between(
                self._source, item, name=self._name))
        if len(refs) > 0:
            self._service.delete_reference_by_name(refs[0].__name__)
            return refs[0]
        return None

    def clear(self):
        self._service.delete_references(self._source, name=self._name)

    def __contains__(self, item):
        refs = list(self._service.get_references_between(
                self._source, item, name=self._name))
        return len(refs) > 0

    def __iter__(self):
        for reference in self.get_references():
            yield get_content_from_id(reference.target_id)


class BrokenReferenceError(BadRequest):
    """The processing of the request will break an existing reference.
    """
    def __init__(self, reference):
        super(BrokenReferenceError, self).__init__(reference)
        self.reference = reference


@grok.subscribe(IReferable, IRelationTargetDeletedEvent)
def reference_target_deleted(content, event):
    event.relation.cleanup()
