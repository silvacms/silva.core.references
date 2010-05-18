# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Acquisition import aq_parent
import AccessControl
from Products.Formulator.Field import ZMIField
from Products.Formulator.FieldRegistry import FieldRegistry
from Products.Formulator.Validator import Validator, StringBaseValidator
from Products.Formulator.Widget import Widget, render_element
from Products.Formulator.DummyField import fields

from five import grok
from silva.core.interfaces import IVersion, ISilvaObject
from zope.component import queryUtility
from zope.interface.interfaces import IInterface
from zope.traversing.browser import absoluteURL


class InterfaceValidator(Validator):
    """Formulator validator for an interface.
    """

    property_names = Validator.property_names + ['required']
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
        value = REQUEST.get(key, "")
        if field.get_value('required') and value == "":
            self.raise_error('required_not_found', field)
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


class BindedReferenceWidget(object):

    template = grok.PageTemplateFile('reference_input.pt')

    def __init__(self, context, request, field, value):
        self.context = context
        self.request = request
        # For security
        self.__parent__ = context
        # For the widget
        self.id = field.getId()
        self.name = field.getId()
        self.title = field.title()
        self.interface = field.get_interface()
        self.value = value
        self.value_title = None
        self.value_url = None
        context_lookup = self.context
        if IVersion.providedBy(context_lookup):
            context_lookup = context_lookup.object()
        self.context_lookup_url = absoluteURL(context_lookup, self.request)

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
        description='default value',
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
        # REQUEST is None. So hack to find it again. By default we
        # can the Silva model as context, if it is present, or the
        # field in the later case.
        request = get_request()
        context = request.get('model', field)
        widget = BindedReferenceWidget(context, request, field, value)
        return widget()



class ReferenceField(ZMIField):
    """Formulator reference field.
    """
    meta_type = "ReferenceField"
    widget = ReferenceWidget()
    validator = StringBaseValidator()

    @property
    def REQUEST(self):
        # Hack for then the field is displayed with broken dummies
        return get_request()

    def getPhysicalRoot(self):
        # This method is hacked in order to work when the field is
        # displayed in ZMI, with broken dummies everything
        parent = aq_parent(self)
        if parent is None:
            return self
        return parent.getPhysicalRoot()

    def get_interface(self):
        try:
            interface = self.get_value('interface')
        except KeyError:
            interface = ISilvaObject
        return interface.__identifier__


# This get initialized by Grok and register the formulator widget
FieldRegistry.registerField(ReferenceField, 'www/BasicField.gif')
