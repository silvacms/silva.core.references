# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import interface
from dolmen.relations.interfaces import ITaggedRelationValue
from silva.core.interfaces import ISilvaService


class IReferenceValue(ITaggedRelationValue):
    """Identify a reference between two Silva content.
    """


class IReferenceService(ISilvaService):
    """Reference Service, used to manage references.
    """

    def new_reference(content, name=None):
        """Create a new reference.
        """

    def get_reference(content, name=None, add=False):
        """Retrieve an existing reference.
        """

    def delete_reference(content, name=None):
        """Lookup and remove a reference.
        """
