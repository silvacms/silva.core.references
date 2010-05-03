# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from OFS.interfaces import IItem
from dolmen.relations.catalog import RelationCatalog
from dolmen.relations.container import RelationsContainer
from five import grok
from zc.relation.interfaces import ICatalog
from zope import component
from zope.lifecycleevent.interfaces import (
    IObjectCreatedEvent, IObjectCopiedEvent)
from zope.location.interfaces import ISite
import uuid

from silva.core import conf as silvaconf
from silva.core.references.interfaces import IReferenceService
from silva.core.references.reference import ReferenceValue, get_content_id
from silva.core.services.base import SilvaService
from silva.core.views import views as silvaviews


class ReferenceService(SilvaService):
    """This service track existing references between content
    """
    meta_type = 'Silva Reference Service'
    grok.implements(IReferenceService)
    silvaconf.icon('service.png')

    manage_options = (
        {'label':'Broken references', 'action':'manage_brokenreferences'},
        ) + SilvaService.manage_options

    def __init__(self, id):
        super(ReferenceService, self).__init__(id)
        self.catalog = RelationCatalog()
        self.references = RelationsContainer()

    def __create_reference(self, content_id, name=None, target_id=0, tags=None):
        """Create and add a new reference
        """
        if tags is None:
            tags = []
        if name is not None:
            tags.append(name)
        reference = ReferenceValue(content_id, target_id, tags=tags)
        reference_id = str(uuid.uuid4())
        self.references[reference_id] = reference
        return reference

    def new_reference(self, content, name=None):
        """Create a new reference.
        """
        content_id = get_content_id(content)
        return self.__create_reference(content_id, name=name)

    def get_reference(self, content, name=None, add=False):
        """Retrieve an existing reference.
        """
        content_id = get_content_id(content)
        references = list(self.catalog.findRelations(
            {'source_id': content_id, 'tag': name}))
        if not len(references):
            if add is True:
                return self.__create_reference(content_id, name=name)
            return None
        return references[0]

    def get_references_to(self, content):
        """Get all references to the given content.
        """
        content_id = get_content_id(content)
        return self.catalog.findRelations({'target_id': content_id})

    def get_references_from(self, content):
        """Get all references from the given content.
        """
        content_id = get_content_id(content)
        return self.catalog.findRelations({'source_id': content_id})

    def delete_reference(self, content, name=None):
        """Lookup and remove a reference.
        """
        reference = self.get_reference(content, name=name, add=False)
        if reference is not None:
            del self.references[reference.__name__]

    def clone_references(self, content, clone):
        """Clone content reference to clone content.
        """
        content_id = get_content_id(content)
        clone_id = get_content_id(clone)
        references = self.catalog.findRelations({'source_id': content_id})
        for reference in references:
            self.__create_reference(
                clone_id,
                target_id=reference.target_id,
                tags=list(reference.tags))


class ListBrokenReference(silvaviews.ZMIView):
    grok.name('manage_brokenreferences')

    def update(self):
        self.broken_targets = list(self.context.catalog.findRelations(
                {'target_id': 0}))
        self.broken_sources = list(self.context.catalog.findRelations(
                {'source_id': 0}))


@grok.subscribe(IReferenceService, IObjectCreatedEvent)
def configureReferenceService(service, event):
    """Configure the reference after it have been created. Register
    the relation catalog to the root local site.
    """
    root = service.get_root()
    sm = root.getSiteManager()
    sm.registerUtility(service.catalog, ICatalog)


@grok.subscribe(IItem, IObjectCopiedEvent)
def cloneReference(content, event):
    """Clone object references when the object is cloned.
    """
    service = component.queryUtility(IReferenceService)
    if service is not None:
        service.clone_references(event.original, event.object)
