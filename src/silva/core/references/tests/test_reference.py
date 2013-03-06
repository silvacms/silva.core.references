# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope import component

from Products.Silva.testing import FunctionalLayer

from ..interfaces import IReferenceService
from ..reference import ReferenceSet, get_content_id
from ..utils import relative_path, canonical_path


class HelpersTestCase(unittest.TestCase):
    """Test helpers.
    """

    def test_relative_path(self):
        self.assertEqual(
            relative_path(
                ['root', 'folder', 'origin'],
                ['root', 'folder', 'content']),
            ['..', 'content'])
        self.assertEqual(
            relative_path(
                ['root', 'folder', 'origin'],
                ['root', 'folder', 'publication', 'content']),
            ['..', 'publication', 'content'])
        self.assertEqual(
            relative_path(
                ['root', 'folder', 'origin'],
                ['root', 'publication', 'content']),
            ['..', '..', 'publication', 'content'])
        self.assertEqual(
            relative_path(
                ['root', 'publication', 'origin'],
                ['root', 'publication', 'origin', 'content']),
            ['content'])
        self.assertEqual(
            relative_path(
                ['root', 'publication', 'origin'],
                ['root', 'publication', 'origin']),
            ['.'])

    def test_canonical_path(self):
        self.assertEqual(
            canonical_path('/root/silva/docs/2.2'),
            '/root/silva/docs/2.2')
        self.assertEqual(
            canonical_path('folder/.'),
            'folder')
        self.assertEqual(
            canonical_path('/root/../folder/./silva'),
            '/folder/silva')
        self.assertEqual(
            canonical_path('/root/////silva'),
            '/root/silva')
        self.assertEqual(
            canonical_path('/////root/.'),
            '/root')
        self.assertEqual(
            canonical_path('./folder/.'),
            'folder')
        self.assertEqual(
            canonical_path('/folder/'),
            '/folder')

        self.assertRaises(ValueError, canonical_path, '../root/folder')
        self.assertRaises(ValueError, canonical_path, 'root/../../../')
        self.assertRaises(ValueError, canonical_path, '/../')


class ReferenceTestCase(unittest.TestCase):
    """Test references objects.
    """
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory.manage_addPublication('publication', 'Publication')
        factory = self.root.folder.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory.manage_addLink('link', 'Duckduck')
        factory.manage_addPublication('publication', 'Publication')
        factory = self.root.folder.folder.manage_addProduct['Silva']
        factory.manage_addLink('link', 'Infrae')
        self.service = component.getUtility(IReferenceService)

    def test_is_target_inside_container(self):
        """Test is_target_in_container on a reference.
        """
        reference = self.service.new_reference(
            self.root.folder.link, name=u'link')
        reference.set_target(self.root.folder.folder.link)

        self.assertEqual(
            reference.is_target_inside_container(self.root.publication),
            False)
        self.assertEqual(
            reference.is_target_inside_container(self.root.folder),
            True)
        self.assertEqual(
            reference.is_target_inside_container(self.root.folder.folder),
            True)
        self.assertEqual(
            reference.is_target_inside_container(self.root.folder.publication),
            False)

    def test_is_source_inside_container(self):
        """Test is_source_in_container on a reference.
        """
        reference = self.service.new_reference(
            self.root.folder.link, name=u'link')
        reference.set_target(self.root.folder.folder.link)

        self.assertEqual(
            reference.is_source_inside_container(self.root.publication),
            False)
        self.assertEqual(
            reference.is_source_inside_container(self.root.folder),
            True)
        self.assertEqual(
            reference.is_source_inside_container(self.root.folder.folder),
            False)
        self.assertEqual(
            reference.is_source_inside_container(self.root.folder.publication),
            False)

    def test_is_broken_target_inside_container(self):
        """Test is_target_in_container on a broken reference.
        """
        reference = self.service.new_reference(
            self.root.folder.link, name=u'link')
        self.assertEqual(
            reference.is_target_inside_container(self.root.publication),
            False)
        self.assertEqual(
            reference.is_target_inside_container(self.root.folder),
            False)
        self.assertEqual(
            reference.is_target_inside_container(self.root.folder.folder),
            False)
        self.assertEqual(
            reference.is_target_inside_container(self.root.folder.publication),
            False)

    def test_relative_path(self):
        """Test relative_path_to on a reference.
        """
        reference = self.service.new_reference(
            self.root.folder.link, name=u'link')
        reference.set_target(self.root.folder.folder)

        self.assertEqual(
            reference.relative_path_to(self.root.publication),
            ['..', 'folder', 'folder'])
        self.assertEqual(
            reference.relative_path_to(self.root.folder),
            ['folder'])
        self.assertEqual(
            reference.relative_path_to(self.root.folder.folder),
            ['.'])
        self.assertEqual(
            reference.relative_path_to(self.root.folder.link),
            ['..', 'folder'])
        self.assertEqual(
            reference.relative_path_to(self.root.folder.folder.link),
            ['..'])

    def test_broken_relative_path(self):
        """Test relative_path_to on a broken reference.
        """
        reference = self.service.new_reference(
            self.root.folder.link, name=u'link')

        self.assertEqual(
            reference.relative_path_to(self.root.publication), [])
        self.assertEqual(
            reference.relative_path_to(self.root.folder), [])
        self.assertEqual(
            reference.relative_path_to(self.root.folder.folder), [])
        self.assertEqual(
            reference.relative_path_to(self.root.folder.link), [])
        self.assertEqual(
            reference.relative_path_to(self.root.folder.folder.link), [])

    def test_broken_reference(self):
        """Create a reference and set it broken.
        """
        reference = self.service.new_reference(self.root.folder, name=u'link')
        reference.set_target(None)
        self.assertEqual(reference.target, None)
        self.assertEqual(reference.target_id, 0)

        reference = self.service.new_reference(self.root.folder, name=u'other')
        reference.set_target_id(0)
        self.assertEqual(reference.target, None)
        self.assertEqual(reference.target_id, 0)


class ReferenceSetTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory.manage_addMockupVersionedContent('info', 'Information')
        factory.manage_addMockupVersionedContent('code', 'Code base')
        factory.manage_addMockupVersionedContent('contact', 'Contact')

    def test_set_with_ids(self):
        """Test the ReferenceSet works if used with content ids
        instead of ids.
        """
        references = ReferenceSet(self.root.folder, 'test-set')
        self.assertEqual(len(list(references)), 0)
        self.assertEqual(len(references.get()), 0)

        # Set some references using the identifiers
        references.set([get_content_id(self.root.info),
                        get_content_id(self.root.code)])
        self.assertEqual(len(list(references)), 2)
        self.assertEqual(len(references.get()), 2)
        self.assertItemsEqual(
            references.get(),
            [self.root.info, self.root.code])

        # Contains work
        self.assertIn(self.root.info, references)
        self.assertIn(self.root.code, references)
        self.assertNotIn(self.root.contact, references)

        # You can set a second different items
        references.set([get_content_id(self.root.contact),
                        get_content_id(self.root.code)])
        self.assertEqual(len(list(references)), 2)
        self.assertEqual(len(references.get()), 2)
        self.assertItemsEqual(
            references.get(),
            [self.root.contact, self.root.code])

        # Contains work
        self.assertNotIn(self.root.info, references)
        self.assertIn(self.root.code, references)
        self.assertIn(self.root.contact, references)

        # You can set an empty set
        references.set([])
        self.assertEqual(len(list(references)), 0)
        self.assertEqual(len(references.get()), 0)

        self.assertNotIn(self.root.info, references)
        self.assertNotIn(self.root.code, references)
        self.assertNotIn(self.root.contact, references)

    def test_set_with_content(self):
        """Test the ReferenceSet works if used with content.
        """
        references = ReferenceSet(self.root.folder, 'test-set')
        self.assertEqual(len(list(references)), 0)
        self.assertEqual(len(references.get()), 0)

        # Set some references
        references.set([self.root.info, self.root.code])
        self.assertEqual(len(list(references)), 2)
        self.assertEqual(len(references.get()), 2)
        self.assertItemsEqual(
            references.get(),
            [self.root.info, self.root.code])

        # Contains work
        self.assertIn(self.root.info, references)
        self.assertIn(self.root.code, references)
        self.assertNotIn(self.root.contact, references)

        # You can add and remove individual reference
        references.add(self.root.contact)
        self.assertEqual(len(references.get()), 3)
        self.assertEqual(len(list(references)), 3)

        references.remove(self.root.code)
        self.assertEqual(len(references.get()), 2)
        self.assertEqual(len(list(references)), 2)
        self.assertItemsEqual(
            references.get(),
            [self.root.info, self.root.contact])
        self.assertIn(self.root.info, references)
        self.assertNotIn(self.root.code, references)
        self.assertIn(self.root.contact, references)

        # And clear all references
        references.clear()
        self.assertEqual(len(list(references)), 0)
        self.assertEqual(len(references.get()), 0)
        self.assertNotIn(self.root.info, references)
        self.assertNotIn(self.root.code, references)
        self.assertNotIn(self.root.contact, references)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HelpersTestCase))
    suite.addTest(unittest.makeSuite(ReferenceTestCase))
    suite.addTest(unittest.makeSuite(ReferenceSetTestCase))
    return suite
