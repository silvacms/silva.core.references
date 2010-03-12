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
    """Test that the service manage references.
    """

    def afterSetUp(self):
        self.add_folder(self.root, 'folder', 'Folder')
        self.add_folder(self.root, 'cloned_folder', 'Clone')
        self.add_publication(self.root, 'publication', 'Publication')
        self.add_publication(self.root, 'cloned_publication', 'Clone')
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
        # We no references at first
        self.assertEquals(
            list(self.service.get_references_to(self.root.publication)), [])
        self.assertEquals(
            list(self.service.get_references_from(self.root.folder)), [])

        reference = self.service.new_reference(
            self.root.folder, name=u'link')

        self.assertEquals(reference.target, None)
        reference.set_target(self.root.publication)
        self.assertEquals(reference.target, self.root.publication)

        searched_reference = self.service.get_reference(
            self.root.folder, name=u'link')
        self.failUnless(verifyObject(IReferenceValue, searched_reference))
        self.assertEquals(searched_reference.target, self.root.publication)

        # We do have now
        self.assertEquals(
            list(self.service.get_references_to(self.root.publication)),
            [reference])
        self.assertEquals(
            list(self.service.get_references_from(self.root.folder)),
            [reference])

    def test_clone_references(self):
        """Test the clone references method.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Clone reference
        self.service.clone_references(self.root.folder, self.root.cloned_folder)

        # We should find our reference now
        cloned_reference = self.service.get_reference(
            self.root.cloned_folder, name=u'myname')
        self.failUnless(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(cloned_reference.target, self.root.publication)

        # The target has two references to itself
        target_references = list(self.service.get_references_to(
            self.root.publication))
        self.failUnless(len(target_references), 2)
        self.assertEquals(
            list(self.service.get_references_from(self.root.folder)),
            [reference])
        self.assertEquals(
            list(self.service.get_references_from(self.root.cloned_folder)),
            [cloned_reference])

        # You can modify the cloned reference
        cloned_reference.set_target(self.root.cloned_publication)

        # This doesn't change the original reference
        original_reference = self.service.get_reference(
            self.root.folder, name=u'myname')
        self.failUnless(verifyObject(IReferenceValue, original_reference))
        self.assertEquals(original_reference, reference)

        # And the original target only have one reference to itself
        # now, the original one
        self.assertEquals(
            list(self.service.get_references_to(self.root.publication)),
            [original_reference])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    suite.addTest(unittest.makeSuite(ServiceManageReferenceTestCase))
    return suite
