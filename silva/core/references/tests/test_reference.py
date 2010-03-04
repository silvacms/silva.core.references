# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from Products.Silva.tests import SilvaTestCase
from zope import component
from zope.interface.verify import verifyObject
from silva.core.references.interfaces import IReferenceService, IReferenceValue


class ServiceTestCase(SilvaTestCase.SilvaTestCase):
    """Test reference system.
    """

    def test_service_implementation(self):
        """Test the service installation and interface. It should be
        available by default.
        """
        service = component.getUtility(IReferenceService)
        self.failUnless(verifyObject(IReferenceService, service))


class ServiceManageReferenceTestCase(SilvaTestCase.SilvaTestCase):
    """Test that the service to manage references.
    """

    def afterSetUp(self):
        self.add_folder(self.root, 'folder', 'Folder')
        self.add_publication(self.root, 'publication', 'Publication')
        self.service = component.getUtility(IReferenceService)

    def test_new_reference(self):
        """Test reference creation.
        """
        # Step one, create a reference
        reference = self.service.new_reference(
            self.root.folder, name=u'link')

        self.failUnless(verifyObject(IReferenceValue, reference))
        self.assertEquals(reference.source, self.root.folder)
        self.assertEquals(reference.tags, [u'link'])

        # You can get back the reference later on
        searched_reference = self.service.get_reference(
            self.root.folder, name=u'link')
        self.failUnless(verifyObject(IReferenceValue, searched_reference))
        self.assertEquals(searched_reference, reference)

        # With a different name, it won't work
        searched_reference = self.service.get_reference(
            self.root.folder, name=u'folder')
        self.assertEquals(searched_reference, None)

    def test_get_and_create_reference(self):
        """Test creation if you give add=True to get_reference.
        """
        reference = self.service.get_reference(
            self.root.folder, name=u'test')
        self.assertEquals(reference, None)

        reference = self.service.get_reference(
            self.root.folder, name=u'test', add=True)
        self.failUnless(verifyObject(IReferenceValue, reference))
        self.assertEquals(reference.source, self.root.folder)
        self.assertEquals(reference.tags, [u'test'])

        reference = self.service.get_reference(
            self.root.publication, name=u"test")
        self.assertEquals(reference, None)

    def test_delete_reference(self):
        """Add, search, remove and search a reference.
        """
        reference = self.service.get_reference(
            self.root.folder, name=u'folder', add=True)
        self.failUnless(verifyObject(IReferenceValue, reference))

        self.service.delete_reference(
            self.root.folder, name=u"folder")

        searched_reference = self.service.get_reference(
            self.root.folder, name=u'folder')
        self.assertEquals(searched_reference, None)

    def test_set_reference_target(self):
        """We create and use a reference, setting its target.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'link')

        references_to = list(self.service.get_references_to(
                self.root.publication))
        self.assertEquals(len(references_to), 0)

        self.assertEquals(reference.target, None)
        reference.set_target(self.root.publication)
        self.assertEquals(reference.target, self.root.publication)

        searched_reference = self.service.get_reference(
            self.root.folder, name=u'link')
        self.failUnless(verifyObject(IReferenceValue, searched_reference))
        self.assertEquals(searched_reference.target, self.root.publication)

        references_to = list(self.service.get_references_to(
                self.root.publication))
        self.assertEquals(len(references_to), 1)
        self.assertEquals(references_to[0], reference)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    suite.addTest(unittest.makeSuite(ServiceManageReferenceTestCase))
    return suite
