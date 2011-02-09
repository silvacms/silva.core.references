# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from zope import component

from Products.Silva.testing import FunctionalLayer

from silva.core.references.reference import relative_path, canonical_path
from silva.core.references.interfaces import IReferenceService


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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HelpersTestCase))
    suite.addTest(unittest.makeSuite(ReferenceTestCase))
    return suite
