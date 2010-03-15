# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from OFS.interfaces import IObjectWillBeRemovedEvent
from dolmen.relations.events import IRelationTargetDeletedEvent
from dolmen.relations.events import RelationModifiedEvent
from dolmen.relations.values import TaggedRelationValue, RelationValue
from zope import component, interface, schema
from zope.event import notify
from zope.intid.interfaces import IIntIds
from five import grok

from silva.core.views import views as silvaviews
from silva.core.interfaces import ISilvaObject
from silva.core.references.interfaces import (
    IReferenceValue, IReferenceService, IReference,
    IDeleteSourceOnTargetDeletion, IContentScheduledForDeletion)

from Acquisition import aq_parent
from zExceptions import BadRequest
import transaction


def get_content_id(content):
    utility = component.getUtility(IIntIds)
    return utility.register(content)


class Reference(schema.Field):
    """Store a reference to an object.
    """
    interface.implements(IReference)

    missing_value = None

    def _validate(self, value):
        # No validation for the moment
        pass


class ReferenceValue(TaggedRelationValue):
    """Store a reference information.
    """
    interface.implements(IReferenceValue)

    def add_tag(self, name):
        assert isinstance(name, unicode), 'The tag must be a unicode string'
        self.tags.append(name)
        notify(RelationModifiedEvent(self))

    def set_target_id(self, target_id):
        self.target_id = target_id
        notify(RelationModifiedEvent(self))

    def set_target(self, target):
        self.set_target_id(get_content_id(target))


class ReferenceProperty(object):
    """Represent a reference.
    """

    def __init__(self, name):
        if IReference.providedBy(name):
            name = name.__name__
        assert isinstance(name, unicode), "Name must be a unicode string"
        self.name = name

    def __get__(self, content, cls=None):
        if content is None:
            raise AttributeError()
        service = component.getUtility(IReferenceService)
        reference = service.get_reference(content, name=self.name, add=True)
        return reference.target

    def __set__(self, content, value):
        service = component.getUtility(IReferenceService)
        reference = service.get_reference(content, name=self.name, add=True)
        if value is None:
            reference.set_target_id(0)
        elif isinstance(value, int):
            reference.set_target_id(value)
        else:
            reference.set_target(value)

    def __delete__(self, content):
        service = component.getUtility(IReferenceService)
        service.delete_reference(content, name=self.name)



class BrokenReferenceError(BadRequest):
    """The processing of the request will break an existing reference.
    """


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
    # Scenario 1, it's a relation where we want to delete always the
    # source if the target is removed.
    if IDeleteSourceOnTargetDeletion.providedBy(event.relation):
        parent_of_source = aq_parent(source)
        parent_of_source.manage_delObjects([source.getId(),])
        return
    # Scenario 2, does the source have been marked for deletion or not
    if not IContentScheduledForDeletion.providedBy(source):
        # We cancel everything, it might work in most case to just do
        # transaction.abort()
        transaction.abort()
        raise BrokenReferenceError(event.relation)


class BrokenReferenceErrorMessage(silvaviews.SMIView):
    grok.context(BrokenReferenceError)
    grok.name('error.html')

    def update(self):
        self.response.setStatus(406)

