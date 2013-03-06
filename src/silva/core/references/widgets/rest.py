# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import operator

from Acquisition import aq_parent

from five import grok
from megrok import pagetemplate as pt
from zope.component import queryUtility, getUtility
from zope.component.interfaces import IFactory
from zope.interface.interfaces import IInterface
from zope.interface import alsoProvides
from zope.intid.interfaces import IIntIds
from zope.traversing.browser import absoluteURL
from zope.cachedescriptors.property import Lazy

from infrae.rest import RESTWithTemplate
from silva.ui.rest import UIREST
from silva.core import interfaces
from silva.core.interfaces import IAddableContents
from silva.core.interfaces.adapters import IIconResolver
from silva.translations import translate as _
from silva.ui.interfaces import ISilvaUI
from zeam.form import silva as silvaforms


from Products.Silva.ExtensionRegistry import meta_types_for_interface
from zExceptions import NotFound


class Items(UIREST):
    """Return information about an item.
    """
    grok.context(interfaces.ISilvaObject)
    grok.require('silva.ReadSilvaContent')
    grok.name('silva.core.references.items')

    def prepare(self):
        # We cannot put this in the __init__ as we don't have the layer set yet
        self.intid = getUtility(IIntIds)
        self.get_icon = IIconResolver(self.request).get_content_url

    def get_item_details(self, content, content_id=None, require=None,
                         show_index=False):
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
            'title': content.get_title_or_id_editable(),
            'short_title': content.get_short_title_editable()}

    def get_context_details(self, require, show_index=False):
        return [self.get_item_details(self.context, content_id='.', require=require)]

    def GET(self, intid=None, interface=None, show_index=False):
        self.prepare()
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
                        'icon': self.get_icon(None),
                        'implements': False,
                        'folderish': False,
                        'title': self.translate(_(u'Missing content')),
                        'short_title': self.translate(_(u'Missing content'))})
            return self.json_response(self.get_item_details(content))
        require = interfaces.ISilvaObject
        if interface is not None:
            require = getUtility(IInterface, name=interface)
        return self.json_response(
            self.get_context_details(require=require, show_index=show_index))


class ContainerItems(Items):
    """Return information on items in a container.
    """
    grok.context(interfaces.IContainer)

    def index(self):
        index = self.context._getOb('index', None)
        if index is not None:
            yield index

    def get_context_details(self, require, show_index=False):
        self.prepare()
        details = super(ContainerItems, self).get_context_details(require)
        providers = []
        if show_index:
            providers.append(self.index)
        providers.extend([self.context.get_ordered_publishables,
                          self.context.get_non_publishables])

        for provider in providers:
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
        self.prepare()
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


class ReferenceLookup(RESTWithTemplate):
    """Return the lookup template.
    """
    grok.context(interfaces.IContainer)
    grok.name('silva.core.references.lookup')
    grok.require('zope2.View')

    def GET(self):
        return self.template.render(self)


class IReferenceAddingUI(ISilvaUI):
    """UI to add content in a reference lookup.
    """


class Adding(UIREST):
    """Add content in context of a reference lookup, or list the
    possible content you can add.
    """
    grok.context(interfaces.IContainer)
    grok.name('silva.core.references.adding')
    grok.require('silva.ChangeSilvaContent')

    @Lazy
    def addables(self):
        return IAddableContents(self.context)

    def publishTraverse(self, request, name):
        if name not in ['GET']:
            addables = self.addables.get_container_addables()
            if name in addables:
                factory = queryUtility(IFactory, name=name)
                if factory is not None:
                    alsoProvides(request, IReferenceAddingUI)
                    factory = factory(self.context, request)
                    # Set parent for security check.
                    factory.__name__ = name
                    factory.__parent__ = self
                    return factory
            raise NotFound()
        return super(Adding, self).publishTraverse(request, name)


    always_allow = [interfaces.IContainer]

    def GET(self, interface=None):
        allowed_addables = self.addables.get_authorized_addables()

        if interface is not None:
            required = getUtility(IInterface, name=interface)
            ifaces = self.always_allow[:]
            # dont append required if it more specific
            # than one in always_allowed
            for iface in ifaces:
                if required.isOrExtends(iface):
                    break
            else:
                ifaces.insert(0, required)

            meta_types = set(reduce(
                    operator.add,
                    map(meta_types_for_interface, ifaces)))
            return self.json_response(
                list(meta_types.intersection(set(allowed_addables))))
        return self.json_response(allowed_addables)


class ReferenceAddFormTemplate(pt.PageTemplate):
    pt.view(silvaforms.SMIAddForm)
    pt.layer(IReferenceAddingUI)
