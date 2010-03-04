# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from Products.Silva.tests import SilvaTestCase
from zope import component
from zope.interface.verify import verifyObject
from silva.core.references.interfaces import IReferenceService, IReferenceValue


class ReferenceServiceTestCase(SilvaTestCase.SilvaTestCase):
    """Test reference system.
    """

    def test_service_implementation(self):
        """Test the service installation and interface. It should be
        available by default.
        """
        service = component.getUtility(IReferenceService)
        self.failUnless(verifyObject(IReferenceService, service))

    def test_new_reference(self):
        """Test reference creation.
        """
        self.add_folder(self.root, 'folder', 'Folder')
        service = component.getUtility(IReferenceService)

        # Step one, create a reference
        reference = service.new_reference(self.root.folder, name=u'link')
        self.failUnless(verifyObject(IReferenceValue, reference))
        self.assertEquals(reference.source, self.root.folder)
        self.assertEquals(reference.tags, [u'link'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ReferenceServiceTestCase))
    return suite
