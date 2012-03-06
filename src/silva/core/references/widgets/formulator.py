# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from operator import attrgetter
import uuid

from Acquisition import aq_parent
import AccessControl
from Products.Formulator.adapters import FieldValueWriter
from Products.Formulator.adapters import FieldValueReader, _marker
from Products.Formulator.Field import ZMIField
from Products.Formulator.FieldRegistry import FieldRegistry
from Products.Formulator.Validator import Validator
from Products.Formulator.Widget import Widget
from Products.Formulator.DummyField import fields

from five import grok
from grokcore.chameleon.components import ChameleonPageTemplate
from zope.interface import Interface

from silva.core.interfaces import ISilvaObject
from silva.core.interfaces.errors import ExternalReferenceError
from silva.core.references.reference import ReferenceSet
from silva.core.references.reference import get_content_from_id
from silva.core.references.utils import relative_path
from silva.core.references.utils import is_inside_container
from silva.core.references.utils import canonical_path
from silva.core.references.widgets import ReferenceInfoResolver
from silva.translations import translate as _

NS_REFERENCES = "http://infrae.com/namespace/silva-references"

def get_request():
    """Return the request when you are lost.
    """
    manager = AccessControl.getSecurityManager()
    return manager.getUser().REQUEST


class ReferencesSolver(object):
    """Object used to delay the references construction on
    deserializeValue.
    """

    def __init__(self, producer):
        self.__info = producer.getInfo()
        self.__contents = []
        self.__expected = 0
        self.__deferreds = []

    def defer(self, callback):
        self.__deferreds.append(callback)

    def add(self, path):
        self.__info.addAction(self.resolve, [path])
        self.__expected += 1

    def resolve(self, path):
        if path:
            imported_path = self.__info.getImportedPath(canonical_path(path))
            if imported_path is not None:
                path = map(str, imported_path.split('/'))
                target = self.__info.root.unrestrictedTraverse(path)
                self.__contents.append(target)
            # else: XXX : report this failure
        self.__expected -= 1
        if not self.__expected:
            for callback in self.__deferreds:
                callback(self.__contents)


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

    def serializeValue(self, field, value, producer):
        if not value:
            return
        settings = producer.getHandler().getSettings()
        if settings.externalRendering():
            return
        root = producer.getHandler().getInfo().root
        if not len(value):
            return
        producer.startPrefixMapping(None, NS_REFERENCES)
        for target in value:
            if value is not None:
                if is_inside_container(root, target):
                    target_path = [root.getId()] + relative_path(
                        root.getPhysicalPath(), target.getPhysicalPath())
                    producer.startElement('path')
                    producer.characters(canonical_path('/'.join(target_path)))
                    producer.endElement('path')
                else:
                    raise ExternalReferenceError(
                        _(u"External reference"),
                        producer.context, target, root)
        producer.endPrefixMapping(None)

    def deserializeValue(self, field, value, context):
        # value should be an lxml node
        solver = ReferencesSolver(context)
        for entry in value.xpath('ref:path', namespaces={'ref': NS_REFERENCES}):
            path = entry.text
            if path is None:
                raise ValueError
            solver.add(path)
        return solver


class ValueInfo(object):
    pass


class BoundReferenceWidget(object):
    """Render a widget.
    """
    template = ChameleonPageTemplate(
        filename='formulator_templates/reference_input.cpt')

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
        self.required = bool(field.get_value('required'))

        css_class = []
        if self.multiple:
            css_class.append('field-multiple')
        if self.required:
            css_class.append('field-required')
        self.css_class = ' '.join(css_class) or None

        self.value = None
        self.reference = None
        self.interface = field.get_interface()

        resolver = ReferenceInfoResolver(self.request)

        if self.multiple:
            self.values = []
            for item in value or []:
                info = ValueInfo()
                resolver(info, self.context, interface=self.interface, value=item)
                self.values.append(info)

            resolver(self, self.context, interface=self.interface)
            self.value = self.values and self.values[0].value or None
            self.extra_values = map(
                attrgetter('value'),
                self.values and self.values[1:] or [])
        else:
            resolver(self, self.context, value=value, interface=self.interface)

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
        default='',
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
        if isinstance(value, basestring) and not len(value):
            # This correspond to empty. However Formulator have
            # problems with that concept.
            value = None
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
        if isinstance(value, ReferencesSolver):
            value.defer(self.__call__)
            return
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
            self._content._p_changed = True
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
