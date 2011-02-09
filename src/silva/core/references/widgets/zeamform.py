# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from zope.interface import Interface

from zeam.form.base.markers import DISPLAY, INPUT, NO_VALUE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField

from silva.core.references.interfaces import IReference
from silva.core.references.reference import get_content_id
from silva.core.references.widgets import ReferenceWidgetInfo


def register():
    registerSchemaField(ReferenceSchemaField, IReference)


class ReferenceSchemaField(SchemaField):
    """Reference field.
    """


class ReferenceWidgetInput(SchemaFieldWidget, ReferenceWidgetInfo):
    grok.adapts(ReferenceSchemaField, Interface, Interface)
    grok.name(str(INPUT))

    def valueToUnicode(self, value):
        return unicode(get_content_id(value))

    def update(self):
        super(ReferenceWidgetInput, self).update()

        interface = self.component.get_field().schema
        interface_name = "%s.%s" % (interface.__module__, interface.__name__)
        self.updateReferenceWidget(
            self.form.context, self.inputValue(),
            interface=interface_name)


class ReferenceWidgetDisplay(ReferenceWidgetInput):
    grok.name(str(DISPLAY))


class ReferenceWidgetExtractor(WidgetExtractor):
    grok.adapts(ReferenceSchemaField, Interface, Interface)

    def extract(self):
        value, error = super(ReferenceWidgetExtractor, self).extract()
        if error is not None:
            return None, error
        if value is NO_VALUE:
            return value, None
        try:
            return int(value), None
        except ValueError:
            None, u"Not a valid content identifier"
