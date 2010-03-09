# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from Acquisition import aq_chain
from Products.Silva.tests import SilvaTestCase
from zope import component
from zope.interface.verify import verifyObject
from silva.core.references.interfaces import IReferenceService, IReferenceValue


class SilvaReferenceTestCase(SilvaTestCase.SilvaTestCase):
    """Test that Silva objects behave with the references (clone,
    copy, paste, move).
    """

    def afterSetUp(self):
        self.add_folder(self.root, 'folder', 'Folder')
        self.add_publication(self.root, 'publication', 'Publication')
        self.add_publication(self.root, 'other', 'Other')
        self.service = component.getUtility(IReferenceService)

    def test_clone(self):
        """Try to clone a Silva object which have references.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Clone folder
        self.root.manage_clone(self.root.folder, 'cloned_folder')

        # The reference should have been cloned
        cloned_reference = self.service.get_reference(
            self.root.cloned_folder, name=u'myname')
        self.failUnless(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(cloned_reference.source, self.root.cloned_folder)
        self.assertEquals(
            aq_chain(cloned_reference.source),
            aq_chain(self.root.cloned_folder))
        self.assertEquals(cloned_reference.target, self.root.publication)
        self.assertEquals(
            aq_chain(cloned_reference.target),
            aq_chain(self.root.publication))

    def test_copy_paste(self):
        """Try to copy and paste a Silva object which have references.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Copy/paste folder
        token = self.root.manage_copyObjects(['folder',])
        self.root.publication.manage_pasteObjects(token)

        # The reference should have been cloned
        cloned_reference = self.service.get_reference(
            self.root.publication.folder, name=u'myname')
        self.failUnless(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(cloned_reference.source, self.root.publication.folder)
        self.assertEquals(
            aq_chain(cloned_reference.source),
            aq_chain(self.root.publication.folder))
        self.assertEquals(cloned_reference.target, self.root.publication)
        self.assertEquals(
            aq_chain(cloned_reference.target),
            aq_chain(self.root.publication))

    def test_source_move(self):
        """Make a reference and move the Silva source around.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Move the source
        token = self.root.manage_cutObjects(['folder',])
        self.root.other.manage_pasteObjects(token)

        # The reference should access the moved source.
        cloned_reference = self.service.get_reference(
            self.root.other.folder, name=u'myname')
        self.failUnless(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(cloned_reference.source, self.root.other.folder)
        self.assertEquals(
            aq_chain(cloned_reference.source),
            aq_chain(self.root.other.folder))
        self.assertEquals(cloned_reference.target, self.root.publication)
        self.assertEquals(
            aq_chain(cloned_reference.target),
            aq_chain(self.root.publication))

    def test_target_move(self):
        """Make a reference and move the target around.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Move the source
        token = self.root.manage_cutObjects(['publication',])
        self.root.other.manage_pasteObjects(token)

        # The reference should access the moved source.
        moved_reference = self.service.get_reference(
            self.root.folder, name=u'myname')
        self.failUnless(verifyObject(IReferenceValue, moved_reference))
        self.assertEquals(moved_reference.source, self.root.folder)
        self.assertEquals(
            aq_chain(moved_reference.source),
            aq_chain(self.root.folder))
        self.assertEquals(moved_reference.target, self.root.other.publication)
        self.assertEquals(
            aq_chain(moved_reference.target),
            aq_chain(self.root.other.publication))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SilvaReferenceTestCase))
    return suite
