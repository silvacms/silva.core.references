# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.traversing.browser import absoluteURL

from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaObject, IVersion, IContainer
from silva.core.interfaces.adapters import IIconResolver
from silva.core.references.reference import get_content_from_id
from silva.core.references.reference import get_content_id
from silva.core.views.interfaces import IVirtualSite
from silva.ui.interfaces import ISilvaUIDependencies
from silva.translations import translate as _


class IReferenceUIResources(ISilvaUIDependencies):
    silvaconf.resource('reference-ui.js')
    silvaconf.resource('reference-ui.css')


def get_lookup_content(content):
    if IVersion.providedBy(content):
        content = content.get_content()
    if (ISilvaObject.providedBy(content) and
        not IContainer.providedBy(content)):
        return content.get_container()
    return content

_marker = object()


class ReferenceInfoResolver(object):
    """This resolve information about a reference and set them on an
    object.
    """

    def __init__(self, request):
        self.request = request
        self.get_icon_tag = IIconResolver(self.request).get_tag
        root = IVirtualSite(self.request).get_root()
        self.root_path = root.absolute_url_path()

    def get_content_path(self, content):
        return content.absolute_url_path()[len(self.root_path):] or '/'

    def defaults(self, widget, context, interface=None):
        widget.interface = interface
        widget.context_lookup_url = absoluteURL(
            get_lookup_content(context), self.request)

    def __call__(self,
                 widget,
                 value_id=_marker,
                 value=_marker,
                 default_msg=_(u"No reference selected.")):
        widget.value_id = None
        widget.value_url = None
        widget.value_title = None
        widget.value_icon = None
        widget.value_path = None

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
            widget.value_id = value_id
        elif value is not _marker:
            widget.value_id = get_content_id(value)
        else:
            return

        # None as a icon, it is missing
        widget.value_icon = self.get_icon_tag(value)
        if value is not None:
            widget.value_title = value.get_title_or_id()
            widget.value_url = absoluteURL(value, self.request)
            widget.value_path = self.get_content_path(value)
        else:
            widget.value_title = default_msg



