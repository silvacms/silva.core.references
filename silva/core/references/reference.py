# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from dolmen.relations.events import RelationModifiedEvent
from dolmen.relations.values import TaggedRelationValue, RelationValue
from zope import component, interface
from zope.event import notify
from zope.intid.interfaces import IIntIds

from silva.core.references.interfaces import IReferenceValue, IReferenceService


def get_content_id(content):
    utility = component.getUtility(IIntIds)
    return utility.getId(content)


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
        self.name = name

    def __get__(self, content, cls=None):
        if content is None:
            raise AttributeError()
        service = component.getUtility(IReferenceService)
        return service.get_reference(content, name=self.name, add=True)

    def __set__(self, content, value):
        raise AttributeError()

    def __delete__(self, content):
        service = component.getUtility(IReferenceService)
        service.delete_reference(content, name=self.name)

