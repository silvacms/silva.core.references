# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from dolmen.relations.catalog import dump, load
from dolmen.relations.container import RelationsContainer
from dolmen.relations.interfaces import IRelationValue
from five import grok
from zc.relation.catalog import Catalog

from silva.core.references.interfaces import IReference, IReferenceService
from silva.core.services.base import SilvaService
from silva.core import conf as silvaconf

import BTrees


class RelationCatalog(Catalog):
    """Catalog references.
    """

    def __init__(self):
        """Create the relation catalog with indexes
        """
        super(RelationCatalog, self).__init__(dump, load)
        self.addValueIndex(IRelationValue['source_id'])
        self.addValueIndex(IRelationValue['target_id'])
        self.addValueIndex(IReference['type'], btree=BTrees.family32.OO)


class ReferenceService(SilvaService):
    """This service track existing references between content
    """
    meta = 'Silva Reference Service'
    grok.implements(IReferenceService)
    silvaconf.factory('manage_addReferenceService')

    def __init__(self):
        self.catalog = RelationCatalog()
        self.references = RelationsContainer()


# XXX: Make a default factory, move register_service and add_and_edit
# in silva.core.conf.
from Products.Silva.helpers import add_and_edit, register_service

def manage_addReferenceService(self, id, REQUEST=None):
    """Add a Reference Service.
    """
    service = ReferenceService(id)
    register_service(self, id, service, IReferenceService)
    add_and_edit(self, id, REQUEST)
    return ''
