# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.schema import interfaces
from zope import schema, interface


class IReference(interfaces.IObject):
    """A reference field is like an object.
    """


class Reference(schema.Field):
    """Store a reference to an object.
    """
    interface.implements(IReference)

    def _validate(self, value):
        # No validation for the moment
        pass
