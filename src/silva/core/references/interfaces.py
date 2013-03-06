# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

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
        """Set the target_id of the relation. It must be an ID
        given by get_content_id or an IntID.
        """

    def set_target(target):
        """Set the target content of the relation.
        """

    def set_source_id(source_id):
        """Set the source_id of the relation. It must an ID given by
        get_content_id or an IntID.
        """

    def set_source(source):
        """Set the source content of the relation.
        """

    def is_target_inside_container(container):
        """Verify that the target of the reference is located inside
        the given container. This always return False if the reference
        as no target.
        """

    def is_source_inside_container(container):
        """Verify that the source of the reference is located inside
        the given container. This always return False if the reference
        as no source.
        """

    def relative_path_to(content):
        """Return the relative path from the given content to the
        target of the reference. This return an empty path only if the
        reference is broken. '.' is returned if content is the same
        object than the target of the reference.
        """


class IWeakReferenceValue(IReferenceValue):
    """ This type of reference will just be deleted without complains
    if the target is deleted.
    """


class IDeleteSourceReferenceValue(IReferenceValue):
    """ This type of reference will delete the source of the reference
    if the target is deleted.
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

    def get_references_to(content, name=None, depth=None):
        """Get all references where the given content is a target,
        optionaly tagged with name.

        If depth is mentioned, search for all content from which
        you can reach the given content in less than depth steps.
        """

    def get_references_from(content, name=None, depth=None):
        """Get all references where the given content is a source,
        optionaly tagged with name.

        If depth is mentioned, search all reacheable content from the
        given content in less than depth steps.
        """

    def get_references_between(source, target, name=None):
        """Get all references binding source and target with an optional
        name.
        """

    def delete_reference(content, name=None):
        """Lookup and remove a single reference.
        """

    def delete_references(content, name=None):
        """Lookup and remove multiple references.
        """

    def clone_references(content, clone, copy_source=None, copy_target=None):
        """Clone content reference to clone content.
        """


class IReferenceGrapher(Interface):
    """Adapt a Silva content to visualize references inside it.
    """

    def dot(stream):
        """Create a graphivz .dot file on the given stream.
        """

    def svg(stream):
        """Create a SVG graph on the given stream.
        """


class IDependenciesReferenceGrapher(Interface):
    """Adapt a Silva content to visualize references from it.
    """
