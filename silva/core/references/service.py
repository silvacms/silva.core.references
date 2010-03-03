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
    meta_type = 'Silva Reference Service'
    grok.implements(IReferenceService)

    def __init__(self, id, title):
        super(ReferenceService, self).__init__(id, title)
        self.catalog = RelationCatalog()
        self.references = RelationsContainer()

