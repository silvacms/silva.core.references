# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Acquisition import aq_parent

from zope import component, interface
from zope.intid.interfaces import IIntIds
from zope.traversing.browser import absoluteURL
from silva.core.interfaces import IVersion
from silva.core.references.interfaces import IReference
from silva.core.references.reference import get_content_id

from z3c.form import interfaces, converter
from z3c.form.widget import Widget, FieldWidget
from z3c.form.browser import widget


class IReferenceWidget(interfaces.IFieldWidget):
    pass


class ReferenceWidget(widget.HTMLInputWidget, Widget):
    """Reference widget implementation.
    """
    interface.implementsOnly(IReferenceWidget)

    def update(self):
        super(ReferenceWidget, self).update()
        # ...
        self.interface = None
        self.value_title = None
        self.value_url = None
        if self.value:
            content = component.getUtility(IIntIds).getObject(int(self.value))
            self.value_title = content.get_title_or_id()
            self.value_url = absoluteURL(content, self.request)
        context_lookup = self.context
        if IVersion.providedBy(context_lookup):
            context_lookup = context_lookup.object()
        self.context_lookup_url = absoluteURL(context_lookup, self.request)


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
