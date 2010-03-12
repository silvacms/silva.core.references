# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.schema.interfaces import IObject
from dolmen.relations.interfaces import ITaggedRelationValue
from silva.core.interfaces import ISilvaService


class IReference(IObject):
    """A reference field is like an object.
    """


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
        """Retrieve an unique existing reference.
        """

    def get_references_to(content):
        """Get all references where the given content is a target.
        """

    def get_references_from(content):
        """Get all references where the given content is a source.
        """

    def delete_reference(content, name=None):
        """Lookup and remove a reference.
        """

    def clone_references(content, clone):
        """Clone content reference to clone content.
        """
