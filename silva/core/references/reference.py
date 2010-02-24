# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import component, interface
from zope.intids.interfaces import IIntIds
from zope.traversing.browser import absoluteURL

from silva.core.references.interfaces import BrokenReferenceError, \
    NotSetReferenceError, IReference


class Reference(object):
    """This object implement a reference.
    """
    interface.implements(IReference)

    def __init__(self, content=None):
        self.__id = None
        if content is not None:
            self.set(content)

    def set(self, content):
        intids = component.getUtility(IIntIds)
        self.__id = intids.registerObject(content)

    def get(self):
        if self.__id is None:
            raise NotSetReferenceError()
        intids = component.getUtility(IIntIds)
        try:
            return intids.getObject(self.__id)
        except KeyError:
            raise BrokenReferenceError()

    def query(self):
        try:
            return self.get()
        except BrokenReferenceError:
            return None

    def url(self, request):
        return absoluteURL(self.get(), request)


class ReferenceDescriptor(object):
    """This descriptor let you access the reference transparently.
    """

    def __init__(self):
        self.reference = Reference()

    def __get__(self, instance):
        return self.reference.get()

    def __set__(self, instance, value):
        return self.reference.get(value)

