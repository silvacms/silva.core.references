# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest
import doctest

from Products.Silva.testing import FunctionalLayer, suite_from_package
from silva.core.interfaces import IAddableContents
from silva.core.references.reference import get_content_id


class RESTAPITestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('author')
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')
        factory.manage_addMockupVersionedContent('index', 'Index')

    def test_rest_adding_list(self):
        """Test REST adding view listing content you can add.
        """
        with self.layer.get_browser() as browser:
            browser.login('author')
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.adding'),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertItemsEqual(
                browser.json,
                IAddableContents(self.root).get_authorized_addables())

    def test_rest_adding_list_interface(self):
        """Test REST adding view listing content you can add that do
        match a give interface.
        """
        with self.layer.get_browser() as browser:
            browser.login('author')
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.adding',
                    query={'interface': 'silva.core.interfaces.content.ILink'}),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertNotIn('Silva Image', browser.json)
            self.assertIn('Silva Folder', browser.json)
            self.assertIn('Silva Link', browser.json)

    def test_rest_adding(self):
        """Test REST adding view that gives you access to a content
        add form.
        """
        with self.layer.get_browser() as browser:
            browser.login('author')
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.adding/Silva Unknown'),
                404)
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.adding/Silva Folder'),
                200)
            self.assertEqual(browser.content_type, 'application/json')

    def test_rest_parents(self):
        """Test REST parents view.
        """
        with self.layer.get_browser() as browser:
            browser.login('author')
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.parents'),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertEqual(len(browser.json), 1)
            self.assertDictContainsSubset(
                {'id': 'root', 'type': 'Silva Root', 'path': '.'},
                browser.json[0])
            self.assertEqual(
                browser.open(
                    '/root/folder/++rest++silva.core.references.parents'),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertEqual(len(browser.json), 2)
            self.assertDictContainsSubset(
                {'id': 'root', 'type': 'Silva Root', 'path': '.'},
                browser.json[0])
            self.assertDictContainsSubset(
                {'id': 'folder', 'type': 'Silva Folder',
                 'path': 'folder', 'title': 'Folder'},
                browser.json[1])

    def test_rest_list(self):
        """Test REST listing items from a container.
        """
        with self.layer.get_browser() as browser:
            browser.login('author')
            # Root
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.items'),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertEqual(len(browser.json), 2)
            self.assertDictContainsSubset(
                {'id': '.', 'type': 'Silva Root', 'path': '.'},
                browser.json[0])
            self.assertDictContainsSubset(
                {'id': 'folder', 'type': 'Silva Folder',
                 'path': 'folder', 'title': 'Folder'},
                browser.json[1])
            # Folder
            self.assertEqual(
                browser.open(
                    '/root/folder/++rest++silva.core.references.items'),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertEqual(len(browser.json), 1)
            self.assertDictContainsSubset(
                {'id': '.', 'type': 'Silva Folder',
                 'path': 'folder', 'title': 'Folder'},
                browser.json[0])
            # Object
            self.assertEqual(
                browser.open(
                    '/root/index/++rest++silva.core.references.items'),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertEqual(len(browser.json), 1)
            self.assertDictContainsSubset(
                {'id': '.', 'type': 'Mockup VersionedContent',
                 'path': 'index', 'title': 'Index'},
                browser.json[0])

    def test_rest_list_show_index(self):
        """Test REST listing items from a container, including the
        indexes.
        """
        with self.layer.get_browser() as browser:
            browser.login('author')
            # Root
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.items',
                    query={'show_index': 'true'}),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertEqual(len(browser.json), 3)
            self.assertDictContainsSubset(
                {'id': '.', 'type': 'Silva Root', 'path': '.'},
                browser.json[0])
            self.assertDictContainsSubset(
                {'id': 'index', 'type': 'Mockup VersionedContent',
                 'path': 'index', 'title': 'Index'},
                browser.json[1])
            self.assertDictContainsSubset(
                {'id': 'folder', 'type': 'Silva Folder',
                 'path': 'folder', 'title': 'Folder'},
                browser.json[2])
            # Folder
            self.assertEqual(
                browser.open(
                    '/root/folder/++rest++silva.core.references.items',
                    query={'show_index': 'true'}),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, list)
            self.assertEqual(len(browser.json), 1)
            self.assertDictContainsSubset(
                {'id': '.', 'type': 'Silva Folder',
                 'path': 'folder', 'title': 'Folder'},
                browser.json[0])

    def test_rest_list_content(self):
        """Test REST listing a give content.
        """
        with self.layer.get_browser() as browser:
            browser.login('author')
            # Working content
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.items',
                    query={'intid': str(get_content_id(self.root.index))}),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, dict)
            self.assertDictContainsSubset(
                {'id': 'index', 'type': 'Mockup VersionedContent',
                 'path': 'index', 'title': 'Index'},
                browser.json)
            # Broken content
            self.assertEqual(
                browser.open(
                    '/root/++rest++silva.core.references.items',
                    query={'intid': '42'}),
                200)
            self.assertEqual(browser.content_type, 'application/json')
            self.assertIsInstance(browser.json, dict)
            self.assertDictContainsSubset(
                {'id': 'broken', 'type': 'Broken',
                 'path': '', 'title': 'Missing content'},
                browser.json)


def create_test(build_test_suite, name):
    test =  build_test_suite(
        name,
        globs={'get_browser': FunctionalLayer.get_browser,
               'get_root': FunctionalLayer.get_application,},
        optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE)
    test.layer = FunctionalLayer
    return test

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RESTAPITestCase))
    suite.addTest(suite_from_package(
            'silva.core.references.tests.widget',
            create_test))
    return suite
