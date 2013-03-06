# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from five.intid.keyreference import KeyReferenceToPersistent
from zope.site.hooks import getSite

from Acquisition import aq_base, aq_chain
from ZPublisher.BaseRequest import RequestContainer
from silva.core.interfaces import IReferable

_marker = object()


class KeyReferenceToIItem(KeyReferenceToPersistent, grok.Adapter):
    grok.context(IReferable)

    @property
    def wrapped_object(self):
        # Change KeyReference not to use unrestricted traverse. This
        # prevent unwanted Acquisition to get a different content that
        # expected if it is gone.
        if self.path is None:
            return self.object

        object = self.root
        for part in self.path.split('/')[1:]:
            object = object._getOb(part, _marker)
            if object is _marker:
                return None

        chain = aq_chain(object)
        # Try to ensure we have a request at the acquisition root
        # by using the one from getSite
        if not len(chain) or not isinstance(chain[-1], RequestContainer):
            site = getSite()
            site_chain = aq_chain(site)
            if (len(site_chain) and
                isinstance(site_chain[-1], RequestContainer)):
                req = site_chain[-1]
                new_obj = req
                # rebuld the chain with the request at the bottom
                for item in reversed(chain):
                    new_obj = aq_base(item).__of__(new_obj)
                obj = new_obj
        return obj
