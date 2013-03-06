# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from Acquisition import aq_chain
from Products.Silva.testing import FunctionalLayer, TestCase

from zope import component
from zope.interface.verify import verifyObject

from ..reference import BrokenReferenceError
from ..reference import WeakReferenceValue, DeleteSourceReferenceValue
from ..reference import ReferenceSet, get_content_from_id
from ..interfaces import IReferenceService, IReferenceValue
from ..interfaces import IDeleteSourceReferenceValue, IWeakReferenceValue


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
        factory = self.root.folder.manage_addProduct['Silva']
        factory.manage_addFolder('contained', 'Contained Folder')
        factory.manage_addFolder('data', 'Data Folder')
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
        self.assertTrue(verifyObject(IReferenceValue, cloned_reference))
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

        self.assertFalse('folder' in self.root.objectIds())
        self.assertTrue('folder' in self.root.publication.objectIds())

        reference = self.service.get_reference(
            self.root.publication.folder, name=u"myname")
        self.assertEqual(reference.target, self.root.publication)
        self.assertEqual(
            len(list(self.service.get_references_to(self.root.publication))),
            1)

    def test_copy_paste_in_same_folder(self):
        """Try to copy and paste a Silva container which is target of
        a reference in the same folder that it is (to duplicate it).
        """
        reference = self.service.new_reference(
            self.root.folder.data, name=u'myname')
        reference.set_target(self.root.folder)

        # Copy/paste folder
        token = self.root.manage_copyObjects(['folder',])
        self.root.manage_pasteObjects(token)

        self.assertTrue('folder' in self.root.objectIds())
        self.assertTrue('copy_of_folder' in self.root.objectIds())

        # Verify the reference.
        cloned_reference = self.service.get_reference(
            self.root.copy_of_folder.data, name=u'myname')
        self.assertTrue(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(
            cloned_reference.source,
            self.root.copy_of_folder.data)
        self.assertEquals(
            aq_chain(cloned_reference.source),
            aq_chain(self.root.copy_of_folder.data))
        self.assertEquals(
            cloned_reference.target,
            self.root.copy_of_folder)
        self.assertEquals(
            aq_chain(cloned_reference.target),
            aq_chain(self.root.copy_of_folder))

        # Each container is the target of one reference.
        self.assertEqual(
            len(list(self.service.get_references_to(self.root.folder))),
            1)
        self.assertEqual(
            len(list(self.service.get_references_to(self.root.copy_of_folder))),
            1)

    def test_copy_paste_source(self):
        """Try to copy and paste a Silva object which have references.
        """
        reference = self.service.new_reference(
            self.root.folder, name=u'myname')
        reference.set_target(self.root.publication)

        # Copy/paste folder
        token = self.root.manage_copyObjects(['folder',])
        self.root.publication.manage_pasteObjects(token)

        self.assertTrue('folder' in self.root.objectIds())
        self.assertTrue('folder' in self.root.publication.objectIds())

        # The reference should have been cloned
        cloned_reference = self.service.get_reference(
            self.root.publication.folder, name=u'myname')
        self.assertTrue(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(
            cloned_reference.source,
            self.root.publication.folder)
        self.assertEquals(
            aq_chain(cloned_reference.source),
            aq_chain(self.root.publication.folder))
        self.assertEquals(
            cloned_reference.target,
            self.root.publication)
        self.assertEquals(
            aq_chain(cloned_reference.target),
            aq_chain(self.root.publication))
        self.assertEqual(
            len(list(self.service.get_references_to(self.root.publication))),
            2)

    def test_copy_paste_contained_source(self):
        """Copy and paste a folder that contained a Silva which have
        references out of this folder.
        """
        reference = self.service.new_reference(
            self.root.folder.contained, name=u'myname')
        reference.set_target(self.root.publication)

        # Copy/paste folder
        token = self.root.manage_copyObjects(['folder',])
        self.root.publication.manage_pasteObjects(token)

        self.assertTrue('folder' in self.root.objectIds())
        self.assertTrue('folder' in self.root.publication.objectIds())

        # The reference should have been cloned
        cloned_reference = self.service.get_reference(
            self.root.publication.folder.contained, name=u'myname')
        self.assertTrue(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(
            cloned_reference.source,
            self.root.publication.folder.contained)
        self.assertEquals(
            aq_chain(cloned_reference.source),
            aq_chain(self.root.publication.folder.contained))
        self.assertEquals(
            cloned_reference.target,
            self.root.publication)
        self.assertEquals(
            aq_chain(cloned_reference.target),
            aq_chain(self.root.publication))
        self.assertEqual(
            len(list(self.service.get_references_to(self.root.publication))),
            2)

    def test_copy_paste_contained_source_and_target(self):
        """Copy and paste a folder that contained a Silva which have
        references in the same folder.
        """
        reference = self.service.new_reference(
            self.root.folder.contained, name=u'myname')
        reference.set_target(self.root.folder.data)

        # Copy/paste folder
        token = self.root.manage_copyObjects(['folder',])
        self.root.publication.manage_pasteObjects(token)

        self.assertTrue('folder' in self.root.objectIds())
        self.assertTrue('folder' in self.root.publication.objectIds())

        # The reference should have been cloned
        cloned_reference = self.service.get_reference(
            self.root.publication.folder.contained, name=u'myname')
        self.assertTrue(verifyObject(IReferenceValue, cloned_reference))
        self.assertEquals(
            cloned_reference.source,
            self.root.publication.folder.contained)
        self.assertEquals(
            aq_chain(cloned_reference.source),
            aq_chain(self.root.publication.folder.contained))
        self.assertEquals(
            cloned_reference.target,
            self.root.publication.folder.data)
        self.assertEquals(
            aq_chain(cloned_reference.target),
            aq_chain(self.root.publication.folder.data))
        self.assertEqual(
            len(list(self.service.get_references_to(
                        self.root.publication.folder.data))),
            1)

        # The original one is not touched
        reference = self.service.get_reference(
            self.root.folder.contained, name=u'myname')
        self.assertTrue(verifyObject(IReferenceValue, reference))
        self.assertEquals(
            reference.source,
            self.root.folder.contained)
        self.assertEquals(
            aq_chain(reference.source),
            aq_chain(self.root.folder.contained))
        self.assertEquals(
            reference.target,
            self.root.folder.data)
        self.assertEquals(
            aq_chain(reference.target),
            aq_chain(self.root.folder.data))
        self.assertEqual(
            len(list(self.service.get_references_to(self.root.folder.data))),
            1)

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
        self.assertTrue(verifyObject(IReferenceValue, cloned_reference))
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
        self.assertTrue(verifyObject(IReferenceValue, moved_reference))
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

    def test_delete_source_no_target(self):
        """We delete a element that is a source of a reference, but
        that reference as no target.
        The reference is just deleted.
        """
        reference = self.service.new_reference(
            self.root.pub.folder.source, name=u"simple reference")

        references = list(self.service.catalog.findRelations({'target_id': 0}))
        self.assertEquals(references, [reference,])
        reference_id = reference.__name__
        self.assertTrue(reference_id in self.service.references.keys())

        self.root.pub.manage_delObjects(['folder'],)

        references = list(self.service.catalog.findRelations({'target_id': 0}))
        self.assertEquals(references, [])
        self.assertFalse(reference_id in self.service.references.keys())

    def test_delete_container_target_outside(self):
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
        self.assertItemsEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.root.pub.manage_delObjects(['folder'],)

        self.assertEquals(list(self.service.get_references_to(target)), [])
        self.assertItemsEqual(self.root.pub.objectIds(), ['source', 'target'])

    def test_delete_container_source_outside(self):
        """Now we delete a folder that contain a content which is a
        target of a reference where the source is not being deleted.

        We should get an error.
        """
        reference = self.service.new_reference(
            self.root.pub.source, name=u"simple reference")
        target = self.root.pub.folder.target
        reference.set_target(target)

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertItemsEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.assertRaises(
            BrokenReferenceError, self.root.pub.manage_delObjects, ['folder'])

    def test_delete_container_with_source_and_target(self):
        """In that test we deleted the source and the target of a
        relation in one shoot by deleting a container that contains
        both of them.

        We should not get any error at all.
        """
        reference = self.service.new_reference(
            self.root.pub.folder.source, name=u"simple reference")
        target = self.root.pub.folder.target
        reference.set_target(target)

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertItemsEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.root.pub.manage_delObjects(['folder'],)

        self.assertEquals(list(self.service.get_references_to(target)), [])
        self.assertItemsEqual(self.root.pub.objectIds(), ['source', 'target'])

    def test_delete_container_with_source_and_target_acquisition_bug(self):
        """In that test we deleted the source and the target of a
        relation in one shoot by deleting a container that contains
        both of them. In addition, one level higher there is a folder
        with the same content and the same id.

        This is a regression bug for five.intid and resolving of deleting ids.
        """
        # Add reference.
        reference = self.service.new_reference(
            self.root.pub.folder.source, name=u"simple reference")
        target = self.root.pub.folder.target
        reference.set_target(target)

        # Add content one level higher with the same ids
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory = self.root.folder.manage_addProduct['Silva']
        factory.manage_addFile('target', 'Target')
        factory.manage_addFile('source', 'Source')

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertItemsEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.root.pub.manage_delObjects(['folder'],)

        self.assertEquals(list(self.service.get_references_to(target)), [])
        self.assertItemsEqual(self.root.pub.objectIds(), ['source', 'target'])

    def test_delete_source_if_delete_target(self):
        """In that test, we want to delete the source anyway if the
        target is deleted.
        """
        reference = self.service.new_reference(
            self.root.pub.source, name=u"simple reference",
            factory=DeleteSourceReferenceValue)
        target = self.root.pub.folder.target
        reference.set_target(target)
        self.assertTrue(verifyObject(IDeleteSourceReferenceValue, reference))

        self.assertEquals(
            list(self.service.get_references_to(target)), [reference])
        self.assertItemsEqual(
            self.root.pub.objectIds(), ['folder', 'source', 'target'])

        self.root.pub.manage_delObjects(['folder'],)

        self.assertEquals(list(self.service.get_references_to(target)), [])
        self.assertItemsEqual(self.root.pub.objectIds(), ['target'])

    def test_delete_weak_reference(self):
        """Delete the target of a weak reference. Nothing wrong should happen.
        """
        reference = self.service.new_reference(
            self.root.pub.source, name=u'weak ref', factory=WeakReferenceValue)
        target = self.root.pub.folder.target
        reference.set_target(target)
        self.assertTrue(verifyObject(IWeakReferenceValue, reference))

        self.root.pub.folder.manage_delObjects(['target'])

    def test_delete_source_and_target(self):
        """We delete both the source and the target of a reference in
        one call to manage_delObjects.
        """
        reference = self.service.new_reference(
            self.root.pub.source, name=u"simple reference")
        reference.set_target(self.root.pub.target)

        self.root.pub.manage_delObjects(['source', 'target'])


class SilvaReferenceSetTestCase(unittest.TestCase):
    """ test silva.core.references.reference.ReferenceSet utility
    """

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('editor')
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory.manage_addLink('link0', 'Link')
        factory.manage_addLink('link1', 'Link')
        factory.manage_addLink('link2', 'Link')
        factory.manage_addLink('link3', 'Link')

        self.links = [self.root.link0,
                 self.root.link1,
                 self.root.link2,
                 self.root.link3]

        self.service = component.getUtility(IReferenceService)

    def test_add_a_relation(self):
        """ A an object to the set and check creation of the reference
        """
        reference_set = ReferenceSet(self.root.folder, u'links')
        reference_set.add(self.links[1])

        self.assertEquals([self.links[1]], list(reference_set))
        refs = list(self.service.get_references_between(self.root.folder,
                                                        self.links[1],
                                                        name=u'links'))
        self.assertEquals(1, len(refs))
        self.assertEquals(self.links[1],
                          get_content_from_id(refs[0].target_id))

    def test_remove_object_from_set(self):
        """ Set a list of objects and remove one
        """
        reference_set = ReferenceSet(self.root.folder, u'links')
        reference_set.set(self.links)
        refs = list(self.service.get_references_from(self.root.folder,
                                                     name=u'links'))
        self.assertEquals(len(self.links), len(refs))

        self.assertTrue(self.links[1] in reference_set)
        removed_ref = reference_set.remove(self.links[1])
        self.assertTrue(removed_ref)
        self.assertTrue(self.links[1] not in reference_set)

        refs = list(self.service.get_references_from(self.root.folder,
                                                     name=u'links'))
        self.assertTrue(removed_ref not in refs)

    def test_set_objects(self):
        """ Test setting objects referenced from a list
        """
        reference_set = ReferenceSet(self.root.folder, u'links')
        reference_set.set(self.links)
        self.assertEquals(set(self.links), set(reference_set))

        reference_set.set(self.links[1:-1])
        self.assertEquals(set(self.links[1:-1]), set(reference_set))


    def test_remove_target_object(self):
        """ Test remove a referenced object from zodb. It should also disappear
        from the reference set.
        """
        reference_set = ReferenceSet(self.root.folder, u'links')
        reference_set.set(self.links)

        self.assertTrue(self.links[1] in reference_set)
        self.root.manage_delObjects(['link1'])
        self.assertTrue(self.links[1] not in reference_set)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SilvaReferenceTestCase))
    suite.addTest(unittest.makeSuite(SilvaReferenceDeletionTestCase))
    suite.addTest(unittest.makeSuite(SilvaReferenceSetTestCase))
    return suite
