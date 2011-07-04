# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import operator

from Acquisition import aq_parent

from five import grok
from silva.ui.rest import UIREST
from silva.core import interfaces
from silva.core.views.interfaces import IVirtualSite
from silva.core.interfaces import IAddableContents
from silva.core.interfaces.adapters import IIconResolver
from zope.interface.interfaces import IInterface
from zope import component
from zope.intid.interfaces import IIntIds
from zope.traversing.browser import absoluteURL

from Products.Silva.ExtensionRegistry import meta_types_for_interface


class Items(UIREST):
    """Return information about an item.
    """
    grok.context(interfaces.ISilvaObject)
    grok.require('silva.ReadSilvaContent')
    grok.name('silva.core.references.items')

    def __init__(self, context, request):
        super(Items, self).__init__(context, request)
        self.intid = component.getUtility(IIntIds)
        site = IVirtualSite(request)
        self.root = site.get_root()
        self.root_url = absoluteURL(self.root, self.request)
        self.get_icon = IIconResolver(self.request).get_content_url

    def get_item_details(self, content, content_id=None, require=None):
        if content_id is None:
            content_id = content.getId()
        return {
            'id': content_id,
            'type': content.meta_type,
            'intid': self.intid.register(content),
            'url': absoluteURL(content, self.request),
            'path': self.get_content_path(content),
            'icon': self.get_icon(content),
            'implements': require and require.providedBy(content) or False,
            'folderish': interfaces.IContainer.providedBy(content),
            'title': content.get_title_or_id(),
            'short_title': content.get_short_title()}

    def get_context_details(self, require):
        details = [self.get_item_details(
                self.context, content_id='.', require=require)]
        if not interfaces.IRoot.providedBy(self.context):
            details.insert(0, self.get_item_details(
                    aq_parent(self.context), content_id='..', require=require))
        return details

    def GET(self, intid=None, interface=None):
        if intid is not None:
            try:
                content = self.intid.getObject(int(intid))
            except KeyError:
                # Invalid content id
                return self.json_response({
                        'id': 'broken',
                        'type': 'Broken',
                        'intid': '0',
                        'url': '', 'path': '',
                        'icon': '/'.join(
                            (self.root_url,
                             '++static++/silva.core.references.widget/exclamation.png')),
                        'implements': False,
                        'folderish': False,
                        'title': 'Broken',
                        'short_title': 'Broken'})
            return self.json_response(self.get_item_details(content))
        require = interfaces.ISilvaObject
        if interface is not None:
            require = component.getUtility(IInterface, name=interface)
        return self.json_response(self.get_context_details(require=require))


class ContainerItems(Items):
    """Return information on items in a container.
    """
    grok.context(interfaces.IContainer)

    def get_context_details(self, require):
        details = super(ContainerItems, self).get_context_details(require)
        for provider in (self.context.get_ordered_publishables,
                         self.context.get_non_publishables):
            for content in provider():
                if (require.providedBy(content) or
                    interfaces.IContainer.providedBy(content)):
                    details.append(self.get_item_details(content, require=require))
        return details


class ParentItems(Items):
    """Return information on parents of an item.
    """
    grok.name('silva.core.references.parents')

    def GET(self):
        details = []
        content = self.context
        while content and not interfaces.IRoot.providedBy(content):
            details.append(self.get_item_details(content))
            content = aq_parent(content)
        # Root element
        if content:
            details.append(self.get_item_details(content))
        details.reverse()
        return self.json_response(details)


class Addables(UIREST):
    """ Return addables in folder
    """
    grok.context(interfaces.IContainer)
    grok.name('silva.core.references.addables')

    always_allow = [interfaces.IContainer]

    def GET(self, interface=None):
        allowed_meta_types = IAddableContents(self.context).get_authorized_addables()

        if interface is not None:
            required = component.getUtility(IInterface, name=interface)
            ifaces = self.always_allow[:]
            # dont append required if it more specific
            # than one in always_allowed
            for iface in ifaces:
                if required.isOrExtends(iface):
                    break
            else:
                ifaces.insert(0, required)

            meta_types = set(reduce(operator.add, map(meta_types_for_interface, ifaces)))
            return self.json_response(list(meta_types.intersection(set(allowed_meta_types))))
        return self.json_response(allowed_meta_types)

