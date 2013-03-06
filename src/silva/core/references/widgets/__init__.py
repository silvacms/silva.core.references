# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from zope.traversing.browser import absoluteURL

from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaObject, IVersion, IContainer
from silva.core.interfaces.adapters import IIconResolver
from silva.core.references.reference import get_content_from_id
from silva.core.references.reference import get_content_id
from silva.core.views.interfaces import IVirtualSite
from silva.ui.interfaces import ISilvaUI
from silva.translations import translate as _


class IReferenceUIResources(ISilvaUI):
    silvaconf.resource('reference.object.js')
    silvaconf.resource('reference.js')
    silvaconf.resource('reference.listing.js')
    silvaconf.resource('reference.adding.js')
    silvaconf.resource('reference.plugins.adding.js')
    silvaconf.resource('reference.plugins.breadcrumbs.js')
    silvaconf.resource('reference.css')


def get_lookup_content(content):
    if IVersion.providedBy(content):
        content = content.get_silva_object()
    if (ISilvaObject.providedBy(content) and
        not IContainer.providedBy(content)):
        return content.get_container()
    return content

_marker = object()


class ReferenceInfoResolver(object):
    """This resolve information about a reference and set them on an
    object.
    """

    def __init__(self, request, context, widget,
                 multiple=False,
                 message=_(u"No reference selected.")):
        self.widget = widget
        self.context = context
        self.request = request
        self.multiple = multiple
        self.message = message
        self.get_icon_tag = IIconResolver(self.request).get_tag
        self.root_path = IVirtualSite(self.request).get_root_path()

    def get_content_path(self, content):
        return content.absolute_url_path()[len(self.root_path):] or '/'

    def set_lookup_url(self, content):
        self.widget.context_lookup_url = absoluteURL(
            get_lookup_content(content), self.request)

    def update(self, interface=None, show_index=False):
        self.widget.show_index = show_index
        self.widget.interface = interface
        self.widget.default_message = self.message
        if self.multiple:
            self.set_lookup_url(self.context)

    def add(self, value_id=_marker, value=_marker, sub_widget=_marker):
        if sub_widget is _marker:
            sub_widget = self.widget
        sub_widget.value_id = None
        sub_widget.value_url = None
        sub_widget.value_title = None
        sub_widget.value_icon = None
        sub_widget.value_path = None

        if value_id is not _marker:
            try:
                value_id = int(value_id)
            except (ValueError, TypeError):
                value_id = 0

            if value is _marker:
                if value_id:
                    value = get_content_from_id(value_id)
                else:
                    value = None
            sub_widget.value_id = value_id
        elif value is not _marker:
            sub_widget.value_id = get_content_id(value)
        else:
            if not self.multiple:
                self.set_lookup_url(self.context)
            return

        # None as a icon, it is missing
        sub_widget.value_icon = self.get_icon_tag(value)
        if value is not None:
            sub_widget.value_title = value.get_title_or_id()
            sub_widget.value_url = absoluteURL(value, self.request)
            sub_widget.value_path = self.get_content_path(value)
            if not self.multiple:
                self.set_lookup_url(value)
        else:
            sub_widget.value_title = self.message
            if not self.multiple:
                self.set_lookup_url(self.context)



