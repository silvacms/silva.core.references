# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.traversing.browser import absoluteURL

from Products.Silva.icon import get_icon_url

from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaObject, IVersion, IContainer
from silva.core.layout.jquery import IJQueryUIResources
from silva.core.references.reference import get_content_from_id
from silva.translations import translate as _


class IReferenceUIResources(IJQueryUIResources):
    silvaconf.resource('reference-ui.js')
    silvaconf.resource('reference-ui.css')


def get_lookup_content(content):
    if IVersion.providedBy(content):
        content = content.object()
    if (ISilvaObject.providedBy(content) and
        not IContainer.providedBy(content)):
        return content.get_container()
    return content


class ReferenceWidgetInfo(object):
    """This provides an update method to computes attributes values
    used by the reference widget templates. This is shared between the
    different form implementation.
    """

    def updateReferenceWidget(self, context, value_id=None, interface=None, value=None):
        self.interface = interface
        self.context_lookup_url = absoluteURL(
            get_lookup_content(context), self.request)

        self.value_url = None
        self.value_title = None
        self.value_icon = None

        try:
            value_id = int(value_id)
        except ValueError:
            value_id = 0

        if value_id:
            value = get_content_from_id(value_id)
        if value is not None:
            self.value_title = value.get_title_or_id()
            self.value_url = absoluteURL(value, self.request)
            self.value_icon = get_icon_url(value, self.request)
        else:
            self.value_title = _('no reference selected')


