# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import zope.component
import zope.interface
import silva.core.references.schema

from z3c.form import interfaces
from z3c.form.widget import Widget, FieldWidget
from z3c.form.browser import widget


class IReferenceWidget(interfaces.IFieldWidget):
    pass


class ReferenceWidget(widget.HTMLTextAreaWidget, Widget):
    """Reference widget implementation.
    """
    zope.interface.implementsOnly(IReferenceWidget)



@zope.component.adapter(
    silva.core.references.schema.IReference, interfaces.IFormLayer)
@zope.interface.implementer(IReferenceWidget)
def ReferenceFieldWidget(field, request):
    """IFieldWidget factory for ReferenceWidget.
    """
    return FieldWidget(field, ReferenceWidget(request))
