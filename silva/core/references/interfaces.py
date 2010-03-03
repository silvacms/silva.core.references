# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import interface
from dolmen.relations.interfaces import IRelationValue
from silva.core.interfaces import ISilvaService


class IReference(IRelationValue):
    """Identify a reference between two Silva content.
    """
    type = interface.Attribute("Type of reference.")


class IReferenceService(ISilvaService):
    """Reference Service, used to manage references.
    """
