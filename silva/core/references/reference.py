# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import component, interface

from dolmen.relations.values import TaggedRelationValue
from silva.core.references.interfaces import IReferenceValue, IReferenceService


class ReferenceValue(TaggedRelationValue):
    """Store a reference information.
    """
    interface.implements(IReferenceValue)



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

