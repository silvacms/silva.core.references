# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from OFS.interfaces import IObjectWillBeRemovedEvent
from dolmen.relations.events import IRelationTargetDeletedEvent
from dolmen.relations.events import RelationModifiedEvent
from dolmen.relations.values import TaggedRelationValue
from zope import component, interface, schema
from zope.event import notify
from zope.intid.interfaces import IIntIds
from five import grok

from silva.core.interfaces import ISilvaObject
from silva.core.references.interfaces import (
    IReferenceValue, IWeakReferenceValue, IReference,
    IDeleteSourceOnTargetDeletion, IContentScheduledForDeletion)

from Acquisition import aq_parent
from zExceptions import BadRequest
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
import transaction


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
    return utility.getObject(int(content_id))


def canonical_path(path):
    """Make a Zope path the smallest possible.
    """
    # XXX should not we work on lists instead of strings ?
    canonical_path = []
    for item in path.split('/'):
        if item == '..':
            if not canonical_path or not canonical_path[-1]:
                raise ValueError("Invalid path")
            canonical_path.pop()
        elif item != '.':
            if item == '' and canonical_path:
                continue
            canonical_path.append(item)
    return '/'.join(canonical_path)


def relative_path(path_orig, path_dest):
    """Takes two path as list of ids and return a new path that is the
    relative path the second against the first.
    """
    path_orig = list(path_orig)
    path_dest = list(path_dest)
    while ((path_orig and path_dest) and
           (path_orig[0] == path_dest[0])):
        path_orig.pop(0)
        path_dest.pop(0)
    result_path = ['..'] * len(path_orig)
    result_path.extend(path_dest)
    if not result_path:
        return ['.']
    return result_path


def is_inside_container(container, content):
    """Tell you if a given content is inside the container. This is
    done by a comparaison on the object paths.
    """
    if content is None:
        # The reference is broken
        return False
    content_path = content.getPhysicalPath()
    container_path = container.getPhysicalPath()
    if len(content_path) < len(container_path):
        return False
    return container_path == content_path[:len(container_path)]


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
        if IDeleteSourceOnTargetDeletion.providedBy(self):
            parent_of_source = aq_parent(self.source)
            parent_of_source.manage_delObjects([self.source.getId(),])
            return
        # the source have been marked for deletion or not
        if not IContentScheduledForDeletion.providedBy(self.source):
            transaction.abort()
            raise BrokenReferenceError(self)


InitializeClass(ReferenceValue)


class WeakReferenceValue(ReferenceValue):
    """ This reference type do not enforce the relation to be kept
    """
    grok.implements(IWeakReferenceValue)

    def cleanup(self):
        if IDeleteSourceOnTargetDeletion.providedBy(self):
            parent_of_source = aq_parent(self.source)
            parent_of_source.manage_delObjects([self.source.getId(),])
            return


class BrokenReferenceError(BadRequest):
    """The processing of the request will break an existing reference.
    """
    def __init__(self, reference):
        super(BrokenReferenceError, self).__init__(reference)
        self.reference = reference


@grok.subscribe(ISilvaObject, IObjectWillBeRemovedEvent)
def mark_content_to_be_deleted(content, event):
    interface.alsoProvides(content, IContentScheduledForDeletion)


@grok.subscribe(ISilvaObject, IRelationTargetDeletedEvent)
def reference_target_deleted(content, event):
    try:
        source = event.relation.source
    except KeyError:
        # Due to a bug in five.intid we cannot retrieve the source
        # anymore. It doesn't mean that it have been removed, it is
        # just that the parent folder have already been removed from
        # the tree, and so is not accessible anymore. five.intid fail
        # traversing through it when it rebuild the acquisition chain
        # to the object. Adding a KeyError to a try: except: in
        # five.intid would help to fix this. In any of the following
        # scenario it is still alright for us.
        return
    event.relation.cleanup()

