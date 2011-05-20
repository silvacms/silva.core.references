# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import uuid

from Acquisition import aq_parent
import AccessControl
from Products.Formulator.adapters import FieldValueWriter
from Products.Formulator.adapters import FieldValueReader, _marker
from Products.Formulator.Field import ZMIField
from Products.Formulator.FieldRegistry import FieldRegistry
from Products.Formulator.Validator import Validator
from Products.Formulator.Widget import Widget, render_element
from Products.Formulator.DummyField import fields

from five import grok
from zope.component import getUtility, queryUtility
from zope.interface import Interface
from zope.interface.interfaces import IInterface

from silva.core.interfaces import ISilvaObject
from silva.core.references.reference import ReferenceSet
from silva.core.references.reference import get_content_from_id
from silva.core.references.reference import get_content_id
from silva.core.references.interfaces import IReferenceService
from silva.core.references.widgets import ReferenceWidgetInfo


class InterfaceValidator(Validator):
    """Formulator validator for an interface.
    """
    property_names = Validator.property_names + [
        'required']
    message_names = Validator.message_names + [
        'required_not_found', 'invalid_interface']

    required = fields.CheckBoxField(
        'required',
        title='Required',
        description=(
            u"Checked if the field is required; the user has to fill in some "
            u"data."),
        default=1)

    invalid_interface = u"Input is not a valid interface."
    required_not_found = u"Input is required but no input given."

    def validate(self, field, key, REQUEST):
        value = REQUEST.get(key)
        if value is None:
            if field.get_value('required'):
                self.raise_error('required_not_found', field)
            return None
        interface = queryUtility(IInterface, name=value.strip())
        if interface is None:
            self.raise_error('invalid_interface', field)
        return interface


class InterfaceWidget(Widget):

    default = fields.InterfaceField(
        'default',
        title='Default',
        description='default value',
        default=None,
        required=0)

    def render(self, field, key, value, REQUEST):
        """Render text input field.
        """
        kw = {'type': "text",
              'name' : key,
              'css_class' : field.get_value('css_class'),
              'value' : value is not None and value.__identifier__ or "",
              'size' : 20,
              'id': field.generate_field_html_id(key)}
        return render_element("input", **kw)


class InterfaceField(ZMIField):
    """Formulator field to select an interface.
    """
    meta_type = "InterfaceField"
    widget = InterfaceWidget()
    validator = InterfaceValidator()


# This get initialized by Grok and register the formulator widget
FieldRegistry.registerField(InterfaceField, 'www/BasicField.gif')

def get_request():
    """Return the request when you are lost.
    """
    manager = AccessControl.getSecurityManager()
    return manager.getUser().REQUEST


class ReferenceValidator(Validator):
    """Extract and validate a reference.
    """
    property_names = Validator.property_names + [
        'required']
    message_names = Validator.message_names + [
        'required_not_found', 'invalid_value']

    required = fields.CheckBoxField(
        'required',
        title='Required',
        description=(
            u"Checked if the field is required; the user has to fill in some "
            u"data."),
        default=1)

    required_not_found = u"Input is required but no input given."
    invalid_value = u"Input is incorrect"

    def validate(self, field, key, REQUEST):
        multiple = bool(field.get_value('multiple'))
        value = REQUEST.form.get(key, None)

        def convert(identifier):
            try:
                return get_content_from_id(identifier)
            except ValueError:
                self.raise_error('invalid_value', field)
        if value:
            if multiple:
                if not isinstance(value, list):
                    value = [value]
                return map(convert, value)
            return convert(value)
        if field.get_value('required'):
            self.raise_error('required_not_found', field)
        return None


class BoundReferenceWidget(ReferenceWidgetInfo):
    """Render a widget.
    """
    template = grok.PageTemplateFile('formulator_templates/reference_input.pt')

    def __init__(self, context, request, field, value):
        self.context = context
        self.request = request
        # For security
        self.__parent__ = context

        # For the widget
        self.id = field.generate_field_html_id()
        self.name = field.generate_field_key()
        self.title = field.title()
        self.multiple = bool(field.get_value('multiple'))

        self.value = None
        self.reference = None
        self.interface = field.get_interface()

        def update_info(info, value, index=0):
            if index == 0:
                info.suffix = ""
            else:
                info.suffix = str(index)

            if ISilvaObject.providedBy(value):
                info.value = get_content_id(value)
                info.reference = None
            else:
                if value and isinstance(value, basestring):
                    # We have a value. It is a tag of the reference. We
                    # want here to lookup the value of the reference.
                    service = getUtility(IReferenceService)
                    reference = service.get_reference(info.context, name=value)
                    info.reference = reference.target_id if reference is not None else 'new'
                    info.value = value
                value = None

        if self.multiple:
            self.values_info = []
            for index, item in enumerate(value or []):
                ref_info = ReferenceWidgetInfo()
                ref_info.request = self.request
                update_info(ref_info, item, index=index)
                ref_info.update_reference_widget(
                    self.context, ref_info.value, value=item,
                    interface=self.interface)
                self.values_info.append(ref_info)
            self.update_reference_widget(self.context,
                interface=self.interface)
        else:
            update_info(self, value)
            self.update_reference_widget(self.context, self.value,
                value=value, interface=self.interface)

    def default_namespace(self):
        return {'context': self.context,
                'request': self.request,
                'view': self}

    def namespace(self):
        return {}

    def __call__(self):
        return self.template.render(self)


class ReferenceWidget(Widget):
    """Widget to select a reference.
    """
    property_names = Widget.property_names + ['interface', 'multiple']

    default = fields.ReferenceField(
        'default',
        title='Default',
        description='Default value (not supported, required by Formulator)',
        default="",
        required=0)

    interface = fields.InterfaceField(
        'interface',
        title='Interface',
        description='Interface that selected contents must comply with.',
        default=ISilvaObject,
        required=1)

    multiple = fields.CheckBoxField(
        'multiple',
        title='Multiple',
        description=(u'If checked, multiple contents can be selected as target '
                     u'of the reference'),
        default=0,
        required=1)

    def render(self, field, key, value, REQUEST):
        # REQUEST is None. So hack to find it again.
        # The context of the form is the acquisition context of this form.
        context = aq_parent(aq_parent(field))
        if context is None:
            return u'<p>Not available.</p>'
        request = get_request()
        widget = BoundReferenceWidget(context, request, field, value)
        return widget()



class ReferenceField(ZMIField):
    """Formulator reference field.
    """
    meta_type = "ReferenceField"
    widget = ReferenceWidget()
    validator = ReferenceValidator()

    def get_interface(self):
        try:
            interface = self.get_value('interface')
        except KeyError:
            interface = ISilvaObject
        return interface.__identifier__


# This get initialized by Grok and register the formulator widget
FieldRegistry.registerField(ReferenceField, 'www/BasicField.gif')


class ReferenceValueWriter(FieldValueWriter):
    grok.adapts(ReferenceField, Interface)

    def __init__(self, field, form):
        self._field = field
        self._content = form.get_content()
        self._context = form.context

    def erase(self):
        if self._field.id in self._content.__dict__:
            identifier = self._content.__dict__[self._field.id]
            references = ReferenceSet(self._context, identifier)
            references.set([])
            del self._content.__dict__[self._field.id]

    def __call__(self, value):
        if self._field.get_value('multiple'):
            assert isinstance(value, list)
        else:
            assert ISilvaObject.providedBy(value)
            value = [value]

        if self._field.id in self._content.__dict__:
            identifier = self._content.__dict__[self._field.id]
        else:
            identifier = unicode(uuid.uuid1())
            self._content.__dict__[self._field.id] = identifier
        references = ReferenceSet(self._context, identifier)
        references.set(value)


class ReferenceValueReader(FieldValueReader):
    grok.adapts(ReferenceField, Interface)

    def __init__(self, field, form):
        self._field = field
        self._content = form.get_content()
        self._context = form.context

    def __call__(self):
        if self._field.id in self._content.__dict__:
            identifier = self._content.__dict__[self._field.id]
            references = list(ReferenceSet(self._context, identifier))
            if len(references):
                if self._field.get_value('multiple'):
                    return references
                return references[0]
        return _marker
