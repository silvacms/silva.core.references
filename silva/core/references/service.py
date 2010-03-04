# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from dolmen.relations.catalog import RelationCatalog
from dolmen.relations.container import RelationsContainer
from five import grok
from zc.relation.interfaces import ICatalog
from zope import component
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.location.interfaces import ISite
import uuid

from silva.core.references.interfaces import IReferenceService
from silva.core.references.reference import ReferenceValue, get_content_id
from silva.core.services.base import SilvaService
from silva.core import conf as silvaconf


class ReferenceService(SilvaService):
    """This service track existing references between content
    """
    meta_type = 'Silva Reference Service'
    grok.implements(IReferenceService)

    def __init__(self, id, title):
        super(ReferenceService, self).__init__(id, title)
        self.catalog = RelationCatalog()
        self.references = RelationsContainer()

    def __create_reference(self, content_id, name):
        """Create and add a new reference
        """
        tags = []
        if name is not None:
            tags.append(name)
        reference = ReferenceValue(content_id, 0, tags=tags)
        reference_id = uuid.uuid1()
        self.references[reference_id] = reference
        return reference

    def new_reference(self, content, name=None):
        """Create a new reference.
        """
        content_id = get_content_id(content)
        return self.__create_reference(content_id, name)

    def get_reference(self, content, name=None, add=False):
        """Retrieve an existing reference.
        """
        content_id = get_content_id(content)
        references = list(self.catalog.findRelations(
            {'source_id': content_id, 'tag': name}))
        if not len(references):
            if add is True:
                return self.__create_reference(content_id, name)
            return None
        return references[0]

    def get_references_to(self, content):
        """Get all references to the given content.
        """
        content_id = get_content_id(content)
        return self.catalog.findRelations({'target_id': content_id})

    def delete_reference(self, content, name=None):
        """Lookup and remove a reference.
        """
        reference = self.get_reference(content, name=name, add=False)
        if reference is not None:
            del self.references[reference.__name__]


@grok.subscribe(IReferenceService, IObjectCreatedEvent)
def configureReferenceService(service, event):
    """Configure the reference after it have been created. Register
    the relation catalog to the root local site.
    """
    root = service.get_root()
    sm = root.getSiteManager()
    sm.registerUtility(service.catalog, ICatalog)
