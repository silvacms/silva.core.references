# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest
import transaction

from Acquisition import aq_chain
from Products.Silva.testing import FunctionalLayer, TestCase

from zope import component, interface
from zope.interface.verify import verifyObject

from silva.core.references.reference import BrokenReferenceError
from silva.core.references.reference import WeakReferenceValue
from silva.core.references.interfaces import IReferenceService, IReferenceValue
from silva.core.references.interfaces import IDeleteSourceOnTargetDeletion


class SilvaReferenceTestCase(unittest.TestCase):
    """Test that Silva objects behave with the references (clone,
    copy, paste, move).
    """
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('editor')
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory.manage_addPublication('publication', 'Publication')
        factory.manage_addPublication('other', 'Other')
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

    def test_cut_paste(self):
        """Try to cut and paste a Silva object which have
        references. They should be copied as well.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Cut/paste folder
        token = self.root.manage_cutObjects(['folder',])
        self.root.publication.manage_pasteObjects(token)

        self.failIf('folder' in self.root.objectIds())
        self.failUnless('folder' in self.root.publication.objectIds())

        reference = self.service.get_reference(
            self.root.publication.folder, name=u"myname")
        self.assertEqual(reference.target, self.root.publication)

    def test_source_copy_paste(self):
        """Try to copy and paste a Silva object which have references.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Copy/paste folder
        token = self.root.manage_copyObjects(['folder',])
        self.root.publication.manage_pasteObjects(token)

        self.failUnless('folder' in self.root.objectIds())
        self.failUnless('folder' in self.root.publication.objectIds())

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


class SilvaReferenceDeletionTestCase(TestCase):
    """Test various scenario on Silva content deletion: if a reference
    would be broken by that deletion, an error will be triggered.
    """
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('editor')
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addPublication('pub', 'Publication')
        factory = self.root.pub.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory.manage_addFile('target', 'Target')
        factory.manage_addFile('source', 'Source')
        factory = self.root.pub.folder.manage_addProduct['Silva']
        factory.manage_addFile('target', 'Target')
        factory.manage_addFile('source', 'Source')
        self.service = component.getUtility(IReferenceService)

    def test_delete_no_target(self):
        """We delete a element that is a source of a reference, but
        that reference as no target.
        The reference is just deleted.
        """
        reference = self.service.new_reference(
            self.root.pub.folder.source, name=u"simple reference")

        references = list(self.service.catalog.findRelations({'target_id': 0}))
        self.assertEquals(references, [reference,])
        reference_id = reference.__name__
        self.failUnless(reference_id in self.service.references.keys())

        self.root.pub.manage_delObjects(['folder'],)

        references = list(self.service.catalog.findRelations({'target_id': 0}))
        self.assertEquals(references, [])
        self.failIf(reference_id in self.service.references.keys())

    def test_delete_target_outside(self):
        """We now delete a folder that contain a content which is source of a
        reference to a target which is not being deleted.

        We should not get any error, the target should remain and the
        relation should be gone.
        """
        reference = self.service.new_reference(
            self.root.pub.folder.source, name=u"simple reference")
        target = self.root.pub.target
        reference.set_target(target)
        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertListEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.root.pub.manage_delObjects(['folder'],)

        self.assertEquals(list(self.service.get_references_to(target)), [])
        self.assertListEqual(self.root.pub.objectIds(), ['source', 'target'])

    def test_delete_source_outside(self):
        """Now we delete a folder that contain a content which is a
        target of a reference where the source is not being deleted.

        We should get an error.
        """
        reference = self.service.new_reference(
            self.root.pub.source, name=u"simple reference")
        target = self.root.pub.folder.target
        reference.set_target(target)
        # You can't break a reference you create in the same
        # request. So we need to commit here in order to get the
        # transaction.abort() working.
        transaction.commit()

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertListEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.assertRaises(
            BrokenReferenceError, self.root.pub.manage_delObjects, ['folder'])

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertListEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

    def test_delete_source_and_target(self):
        """In that test we deleted the source and the target of a
        relation in one shoot.

        We should not get any error at all.
        """
        reference = self.service.new_reference(
            self.root.pub.folder.source, name=u"simple reference")
        target = self.root.pub.folder.target
        reference.set_target(target)

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertListEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.root.pub.manage_delObjects(['folder'],)

        self.assertEquals(list(self.service.get_references_to(target)), [])
        self.assertListEqual(self.root.pub.objectIds(), ['source', 'target'])

    def test_delete_source_if_delete_target(self):
        """In that test, we want to delete the source anyway if the
        target is deleted.
        """
        reference = self.service.new_reference(
            self.root.pub.source, name=u"simple reference")
        target = self.root.pub.folder.target
        interface.alsoProvides(reference, IDeleteSourceOnTargetDeletion)
        reference.set_target(target)

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertListEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.root.pub.manage_delObjects(['folder'],)

        self.assertEquals(list(self.service.get_references_to(target)), [])
        self.assertListEqual(self.root.pub.objectIds(), ['target'])

    def test_weak_reference(self):
        reference = self.service.new_reference(
            self.root.pub.source, name=u'weak ref', factory=WeakReferenceValue)
        target = self.root.pub.folder.target
        reference.set_target(target)

        self.root.pub.folder.manage_delObjects(['target'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SilvaReferenceTestCase))
    suite.addTest(unittest.makeSuite(SilvaReferenceDeletionTestCase))
    return suite
