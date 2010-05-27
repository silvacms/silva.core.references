# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import component, interface

from z3c.form import interfaces, converter
from z3c.form.widget import Widget, FieldWidget
from z3c.form.browser import widget

from silva.core.references.interfaces import IReference
from silva.core.references.reference import get_content_id
from silva.core.references.widgets import ReferenceWidgetInfo


class IReferenceWidget(interfaces.IFieldWidget):
    pass


class ReferenceWidget(widget.HTMLInputWidget, Widget, ReferenceWidgetInfo):
    """Reference widget implementation.
    """
    interface.implementsOnly(IReferenceWidget)

    def update(self):
        super(ReferenceWidget, self).update()
        self.updateReferenceWidget(self.context, self.value)
        self.interface = None
        self.reference = None


class ReferenceDataConverter(converter.BaseDataConverter):
    """Data converter for ReferenceWidget.
    """
    component.adapts(IReference, IReferenceWidget)

    def toWidgetValue(self, value):
        if value is None:
            return None
        return get_content_id(value)

    def toFieldValue(self, value):
        if not value:
            return None
        return int(value)


@component.adapter(IReference, interfaces.IFormLayer)
@interface.implementer(IReferenceWidget)
def ReferenceFieldWidget(field, request):
    """IFieldWidget factory for ReferenceWidget.
    """
    widget =  FieldWidget(field, ReferenceWidget(request))
    widget.title = field.title  # Set properly the title to have access to it
    return widget
