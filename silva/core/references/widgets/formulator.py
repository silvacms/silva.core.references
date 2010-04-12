# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import AccessControl
from Products.Formulator.Field import ZMIField
from Products.Formulator.FieldRegistry import FieldRegistry
from Products.Formulator.Validator import StringBaseValidator
from Products.Formulator.Widget import Widget
from Products.Formulator.DummyField import fields

from silva.core.interfaces import IVersion
from zope.traversing.browser import absoluteURL
from five import grok


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
        self.interface = field.get_value('interface')
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

    default = fields.ReferenceField(
        'default',
        title='Default',
        description='default value',
        default="",
        required=0)

    interface = fields.StringField(
        'interface',
        title='Interface',
        description='interface that the selected content must comply with',
        default="silva.core.interfaces.content.ISilvaObject",
        required=1)

    def render(self, field, key, value, REQUEST):
        # REQUEST is None. So you have to find it again. By default we
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


# This get initialized by Grok and register the formulator widget
FieldRegistry.registerField(ReferenceField, 'www/BasicField.gif')
