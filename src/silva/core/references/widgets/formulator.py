# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import uuid
import logging

from Acquisition import aq_parent
import AccessControl
from zeam.form.silva.datamanager import FieldValueWriter
from zeam.form.silva.datamanager import FieldValueReader
from Products.Formulator.Field import ZMIField
from Products.Formulator.FieldRegistry import FieldRegistry
from Products.Formulator.Validator import Validator
from Products.Formulator.Widget import Widget
from Products.Formulator.DummyField import fields

from grokcore.chameleon.components import ChameleonPageTemplate
from zope.interface import Interface
from zeam import component

from silva.core.interfaces import ISilvaObject
from silva.core.interfaces.errors import ExternalReferenceError
from silva.core.references.reference import ReferenceSet
from silva.core.references.reference import get_content_from_id
from silva.core.references.utils import relative_path
from silva.core.references.utils import is_inside_container
from silva.core.references.utils import canonical_path
from silva.core.references.widgets import ReferenceInfoResolver
from silva.translations import translate as _


_marker = object()
logger = logging.getLogger('silva.core.references')

NS_REFERENCES = "http://infrae.com/namespace/silva-references"

def get_request():
    """Return the request when you are lost.
    """
    manager = AccessControl.getSecurityManager()
    return manager.getUser().REQUEST


class ReferencesSolver(object):
    """Object used to delay the references resolving in
    deserializeValue:

    - This object is returned instead of the target of the reference
      duing the deserialization.

    - Required setting and callback used to set the resolved
      references are collecting then this object is saved in
      Formulator.

    - The reference is resolved and effectively set when is the import
      of all the others content are done.
    """

    def __init__(self, producer, field):
        self._id = field.getId()
        self._importer = producer.getExtra()
        self._context = None
        self._contents = []
        self._expected = 0
        self._callback = None
        self._single = True

    def report(self, message):
        self._importer.reportProblem(
            "Error in field '{0}': {1}".format(self._id, message),
            self._context)

    def defer(self, callback, single, context):
        assert self._callback is None, 'Defer called twice'
        self._callback = callback
        self._single = single
        self._context = context

    def add(self, path):
        self._importer.addAction(self.resolve, [path])
        self._expected += 1

    def resolve(self, path):
        if path:
            imported_path = self._importer.getImportedPath(canonical_path(path))
            if imported_path is not None:
                path = map(str, imported_path.split('/'))
                try:
                    target = self._importer.root.unrestrictedTraverse(path)
                except (AttributeError, KeyError):
                    self.report(
                        'Could not traverse imported path {0}.'.format(path))
                self._contents.append(target)
            else:
                self.report(
                    'Could not resolve imported path {0}.'.format(path))
        else:
            self.report('Broken reference.')

        self._expected -= 1
        if not self._expected and self._callback is not None:
            if self._single:
                if self._contents:
                    if len(self._contents) != 1:
                        self.reportProblem(
                            'Found multiple paths where only one was expected.')
                    self._callback(self._contents[0])
            else:
                self._callback(self._contents)


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
                content =  get_content_from_id(int(identifier))
            except ValueError:
                self.raise_error('invalid_value', field)
            if ISilvaObject.providedBy(content):
                return content
            return None

        if value:
            if multiple:
                if not isinstance(value, list):
                    value = [value]
                value = filter(lambda v: v is not None, map(convert, value))
                if len(value):
                    return value
            else:
                value = convert(value)
                if value is not None:
                    return value
        if field.get_value('required'):
            self.raise_error('required_not_found', field)
        return value

    def serializeValue(self, field, value, producer):
        if not value:
            return
        handler = producer.getHandler()
        options = handler.getOptions()
        if options.external_rendering:
            return
        if not bool(field.get_value('multiple')):
            value = [value]
        exported = handler.getExported()
        producer.startPrefixMapping(None, NS_REFERENCES)
        for target in value:
            if value is not None:
                if is_inside_container(exported.root, target):
                    target_path = [exported.root.getId()] + relative_path(
                        exported.rootPath, target.getPhysicalPath())
                    producer.startElement('path')
                    producer.characters(canonical_path('/'.join(target_path)))
                    producer.endElement('path')
                else:
                    if options.external_references:
                        exported.reportProblem(
                            (u"A reference field '{0}' refers to an " +
                             u'content outside of the export ({1}).').format(
                                field.getId(),
                                '/'.join(relative_path(
                                        exported.rootPath,
                                        target.getPhysicalPath()))),
                            producer.context)
                        producer.startElement('path')
                        producer.endElement('path')
                    else:
                        raise ExternalReferenceError(
                            _(u"External reference"),
                            producer.context, target, exported.root)
        producer.endPrefixMapping(None)

    def deserializeValue(self, field, value, context):
        # value should be an lxml node
        solver = ReferencesSolver(context, field)
        for entry in value.xpath('ref:path', namespaces={'ref': NS_REFERENCES}):
            solver.add(entry.text)
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
        self.value_id = None
        self.extra_values = []

        resolver = ReferenceInfoResolver(
            self.request, self.context, self,
            multiple=self.multiple,
            message=field.get_value('default_msg') or _(u"No content selected."))
        resolver.update(
            interface=field.get_interface(),
            show_index=field.get_value('show_container_index'))

        if self.multiple:
            self.values = []
            # Support for one value list from the request (string are lists...).
            if isinstance(value, basestring) or not isinstance(value, list):
                if value:
                    value = [value]
                else:
                    value = []
            # Go through each value and prepare information
            for item in value:
                info = ValueInfo()
                if isinstance(item, (basestring, int)):
                    resolver.add(value_id=item, sub_widget=info)
                else:
                    resolver.add(value=item, sub_widget=info)
                self.values.append(info)

            self.value = len(self.values) and self.values[0] or None
            self.extra_values = len(self.values) and self.values[1:] or []
        else:
            # Prepare information
            self.value = ValueInfo()
            if isinstance(value, (basestring, int)):
                resolver.add(value_id=value, sub_widget=self.value)
            else:
                resolver.add(value=value, sub_widget=self.value)

        # Shortcut for template.
        if self.value is not None:
            self.value_id = self.value.value_id

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
    property_names = Widget.property_names + [
        'interface', 'multiple', 'default_msg', 'show_container_index']

    default = fields.ReferenceField(
        'default',
        title=u'Default',
        description=u'Default value (not supported, required by Formulator).',
        default='',
        required=0)

    interface = fields.InterfaceField(
        'interface',
        title=u'Interface',
        description=u'Interface that selected contents must comply with.',
        default=ISilvaObject,
        required=1)

    multiple = fields.CheckBoxField(
        'multiple',
        title='Multiple',
        description=(u'If checked, multiple contents can be selected as target '
                     u'of the reference'),
        default=0,
        required=1)

    show_container_index = fields.CheckBoxField(
        'show_container_index',
        title="Show containers index",
        description=(u"Allows to select containers index as target. "
                     u"In most cases it is not needed; choosing the container "
                     u"itself is preferred."),
        default=0,
        required=1)

    default_msg = fields.StringField(
        'default_msg',
        title=u'Default Message',
        description=(u'Default message displayed to the user if '
                     u'the field is empty.'),
        default='',
        required=0)
    view_separator = fields.StringField(
        'view_separator',
        title='View separator',
        description=(
            "When called with render_view, this separator will be used to "
            "render individual items."),
        width=20,
        default='<br />\n',
        whitespace_preserve=1,
        required=1)

    def render(self, field, key, value, REQUEST):
        # REQUEST is None. So hack to find it again.
        # The context of the form is the acquisition context of this form.
        context = aq_parent(field)
        if context is None:
            return u'<p>Not available.</p>'
        request = get_request()
        if isinstance(value, basestring) and not len(value):
            # This correspond to empty. However Formulator have
            # problems with that concept.
            value = None
        widget = BoundReferenceWidget(context, request, field, value)
        return widget()

    def render_view(self, field, value):

        def render_value(value):
            return value.get_title_or_id()

        if not field.get_value('multiple'):
            value = [value]

        try:
            separator = str(field.get_value('view_separator'))
        except KeyError:
            separator = '<br />\n'
        return separator.join(map(render_value, value))


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
    component.adapts(ReferenceField, Interface)

    def __init__(self, *args):
        super(ReferenceValueWriter, self).__init__(*args)
        self.context = self.form.context

    def delete(self):
        if self.identifier in self.content.__dict__:
            identifier = self.content.__dict__[self.identifier]
            references = ReferenceSet(self.context, identifier)
            references.set([])
            del self.content.__dict__[self.identifier]

    def __call__(self, value):
        multiple = bool(self.field._field.get_value('multiple'))
        if isinstance(value, ReferencesSolver):
            value.defer(self.__call__, not multiple, self.context)
            return
        if value is None:
            value = []
        elif multiple:
            assert isinstance(value, list)
        else:
            assert ISilvaObject.providedBy(value)
            value = [value]

        if self.identifier in self.content.__dict__:
            identifier = self.content.__dict__[self.identifier]
        else:
            identifier = unicode(uuid.uuid1())
            self.content.__dict__[self.identifier] = identifier
            self.content._p_changed = True
        references = ReferenceSet(self.context, identifier)
        references.set(value)


class ReferenceValueReader(FieldValueReader):
    component.adapts(ReferenceField, Interface)

    def __init__(self, *args):
        super(ReferenceValueReader, self).__init__(*args)
        self.context = self.form.context

    def __call__(self, default=None):
        if self.identifier in self.content.__dict__:
            identifier = self.content.__dict__[self.identifier]
            references = list(ReferenceSet(self.context, identifier))
            if len(references):
                if self.field._field.get_value('multiple'):
                    return references
                return references[0]
        return default
