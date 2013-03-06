# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import Interface

from zeam.form.base.markers import DISPLAY, INPUT, NO_VALUE
from zeam.form.base.widgets import FieldWidget, WidgetExtractor
from zeam.form.base.fields import Field
from zeam.form.ztk.fields import registerSchemaField

from silva.core.references.interfaces import IReference
from silva.core.references.reference import get_content_id
from silva.core.references.widgets import ReferenceInfoResolver
from silva.core.references.widgets import IReferenceUIResources
from silva.translations import translate as _
from silva.fanstatic import need


class ReferenceField(Field):
    """Reference field.
    """
    referenceNotSetDisplayLabel = _("No reference selected.")
    referenceNotSetLabel = _("No reference selected.")
    showIndex = False

    def __init__(self, schema=None, **options):
        super(ReferenceField, self).__init__(**options)
        self.schema = schema

    @property
    def schemaName(self):
        return "%s.%s" % (self.schema.__module__, self.schema.__name__)


class ReferenceMultipleField(ReferenceField):
    pass


class ReferenceWidgetInput(FieldWidget):
    grok.adapts(ReferenceField, Interface, Interface)
    grok.name(str(INPUT))
    defaultHtmlClass = ['field', 'field-reference']

    def valueToUnicode(self, value):
        return unicode(get_content_id(value))

    @property
    def referenceLabel(self):
        return self.component.referenceNotSetLabel

    def update(self):
        super(ReferenceWidgetInput, self).update()
        need(IReferenceUIResources)

        resolver = ReferenceInfoResolver(
            self.request, self.form.context, self,
            multiple=False,
            message=self.referenceLabel)
        resolver.update(
            interface=self.component.schemaName,
            show_index=self.component.showIndex)
        resolver.add(value_id=self.inputValue())


class ValueInfo(object):
    pass


class ReferenceMultipleWidgetInput(FieldWidget):
    grok.adapts(ReferenceMultipleField, Interface, Interface)
    grok.name(str(INPUT))
    defaultHtmlClass = ['field', 'field-reference', 'field-multiple']

    def prepareContentValue(self, values):
        resolver = ReferenceInfoResolver(
            self.request, self.form.context, self,
            multiple=True,
            message=self.referenceLabel)
        resolver.update(
            interface=self.component.schemaName,
            show_index=self.component.showIndex)

        self.items = []
        if values is not NO_VALUE and values:
            for value in values:
                info = ValueInfo()
                resolver.add(value=value, sub_widget=info)
                self.items.append(info)

        return {self.identifier: str(len(self.items))}

    def prepareRequestValue(self, values, extractor):
        resolver = ReferenceInfoResolver(
            self.request, self.form.context, self,
            multiple=True,
            message=self.referenceLabel)
        resolver.update(
            interface=self.component.schemaName,
            show_index=self.component.showIndex)
        self.items = []
        # XXX This needs to be implemented
        return {self.identifier: str(len(self.items))}

    @property
    def referenceLabel(self):
        return self.component.referenceNotSetLabel

    def update(self):
        super(ReferenceMultipleWidgetInput, self).update()
        need(IReferenceUIResources)


class ReferenceWidgetDisplay(ReferenceWidgetInput):
    grok.name(str(DISPLAY))

    @property
    def referenceLabel(self):
        return self.component.referenceNotSetDisplayLabel


class ReferenceWidgetExtractor(WidgetExtractor):
    grok.adapts(ReferenceField, Interface, Interface)

    def extract(self):
        value, error = super(ReferenceWidgetExtractor, self).extract()
        if error is not None:
            return None, error
        if value is NO_VALUE or not len(value):
            return NO_VALUE, None
        try:
            return int(value), None
        except ValueError:
            None, u"Not a valid content identifier"


class ReferenceMultipleWidgetExtractor(WidgetExtractor):
    grok.adapts(ReferenceMultipleField, Interface, Interface)

    def extract(self):
        value, error = super(ReferenceMultipleWidgetExtractor, self).extract()
        if error is not None:
            return None, error
        if value is NO_VALUE or not len(value):
            return NO_VALUE, None
        if not isinstance(value, list):
            value = [value]
        try:
            return map(int, value), None
        except ValueError:
            None, u"Invalid content identifiers"


def ReferenceFieldFactory(schema):
    factory = ReferenceField
    if schema.multiple:
        factory = ReferenceMultipleField
    return factory(title=schema.title or None,
                   schema=schema.schema,
                   identifier=schema.__name__,
                   description=schema.description,
                   required=schema.required)


def register():
    registerSchemaField(ReferenceFieldFactory, IReference)
