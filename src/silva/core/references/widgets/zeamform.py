# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from zope.interface import Interface
from zope.traversing.browser import absoluteURL

from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField

from silva.core.references.interfaces import IReference
from silva.core.references.reference import get_content_id
from silva.core.references.widgets import ReferenceWidgetInfo


class ReferenceSchemaField(SchemaField):
    """Reference field.
    """


registerSchemaField(ReferenceSchemaField, IReference)


class ReferenceWidget(SchemaFieldWidget, ReferenceWidgetInfo):
    grok.adapts(ReferenceSchemaField, Interface, Interface)

    def valueToUnicode(self, value):
        return unicode(get_content_id(value))

    def update(self):
        super(ReferenceWidget, self).update()
        self.updateReferenceWidget(self.form.context, self.inputValue())


class ReferenceWidgetExtractor(WidgetExtractor):
    grok.adapts(ReferenceSchemaField, Interface, Interface)

    def extract(self):
        value, error = super(ReferenceWidgetExtractor, self).extract()
        if error is not None:
            return None, error
        try:
            return int(value), None
        except ValueError:
            None, u"Not a valid content identifier"
