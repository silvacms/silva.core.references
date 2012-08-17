# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from AccessControl import ClassSecurityInfo
from Acquisition import aq_parent
from App.class_init import InitializeClass
from zExceptions import BadRequest

from dolmen.relations.events import IRelationTargetDeletedEvent
from dolmen.relations.events import RelationModifiedEvent
from dolmen.relations.values import TaggedRelationValue
from five import grok
from zope import component, interface, schema
from zope.event import notify
from zope.intid.interfaces import IIntIds

from silva.core.interfaces import ISilvaObject, IContainerManager

from .utils import is_inside_container
from .utils import relative_path
from .interfaces import IReferenceValue
from .interfaces import IWeakReferenceValue, IDeleteSourceReferenceValue
from .interfaces import IReference, IReferenceService


def get_content_id(content):
    """Return the ID of a content.
    """
    if content is None:
        return 0
    utility = component.getUtility(IIntIds)
    return utility.register(content)


def get_content_from_id(content_id):
    """Return a content from its ID.
    """
    if content_id == 0:
        return None
    utility = component.getUtility(IIntIds)
    try:
        return utility.getObject(int(content_id))
    except KeyError:
        return None


class Reference(schema.Object):
    """Store a reference to an object.
    """
    interface.implements(IReference)

    missing_value = None

    def _validate(self, value):
        # XXX No validation for the moment
        pass


class ReferenceValue(TaggedRelationValue):
    """Store a reference information.
    """
    interface.implements(IReferenceValue)

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
            self.target.getPhysicalPath())

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
    """ A object wrapper around multiple references relationship between
    a unique source and several objects.
    """

    def __init__(self, source, name, factory=WeakReferenceValue):
        self._source = source
        self._factory = factory
        self._name = unicode(name)
        self._service = component.getUtility(IReferenceService)

    def get_references(self):
        return self._service.get_references_from(
            self._source, name=self._name)

    def set(self, items):
        reference_names = set(map(lambda r: r.__name__, self.get_references()))

        for item in items:
            reference = self.add(item)
            if reference.__name__ in reference_names:
                reference_names.remove(reference.__name__)

        if reference_names:
            for name in reference_names:
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


@grok.subscribe(ISilvaObject, IRelationTargetDeletedEvent)
def reference_target_deleted(content, event):
    event.relation.cleanup()
