# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from dolmen.relations.interfaces import ITaggedRelationValue
from silva.core.interfaces import ISilvaService
from zope.interface import Interface
from zope.schema.interfaces import IObject


class IReference(IObject):
    """A reference field is like an object.
    """


class IReferenceValue(ITaggedRelationValue):
    """Identify a reference between two Silva content.
    """

    def add_tag(name):
        """Add a tag called name to the relation. You can after look
        for the relation using this tag as well.
        """

    def set_target_id(target_id):
        """Set the target_id of the relation. It must be the an ID
        given by get_content_id or an Int ID.
        """

    def set_target(target):
        """Set the target content of the relation.
        """

    def is_target_inside_container(container):
        """Verify that the target of the reference is located inside
        the given container.
        """

    def relative_path_to(content):
        """Return the relative path from the given content to the
        target of the reference.
        """



class IDeleteSourceOnTargetDeletion(Interface):
    """Marker interface for ReferenceValue to indicate that if the
    relation target is deleted, so should the source.
    """


class IContentScheduledForDeletion(Interface):
    """Marker interface to say that this content will be deleted.
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
