# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from dolmen.relations.events import RelationModifiedEvent
from dolmen.relations.values import TaggedRelationValue, RelationValue
from zope import component, interface, schema
from zope.event import notify
from zope.intid.interfaces import IIntIds

from silva.core.references.interfaces import (
    IReferenceValue, IReferenceService, IReference)


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


