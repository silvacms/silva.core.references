# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$


import unittest
import json
from Products.Silva.testing import FunctionalLayer


class RESTAddablesTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')

    def test_rest_api(self):
        browser = self.layer.get_browser()
        browser.login('author')
        self.assertEqual(browser.open('/root/folder/++rest++silva.core.references.addables'), 200)
        self.assertEqual('application/json', browser.content_type)
        data = json.loads(browser.contents)
        self.assertTrue(isinstance(data, list))
        self.assertTrue(len(data) > 0)

    def test_rest_api_with_required_interface(self):
        browser = self.layer.get_browser()
        browser.login('author')
        browser.options.handle_errors = False
        self.assertEqual(
            200,
            browser.open('/root/folder/++rest++silva.core.references.addables',
                query={'interface': 'silva.core.interfaces.content.IImage'}))
        self.assertEqual('application/json', browser.content_type)
        data = json.loads(browser.contents)
        self.assertTrue(isinstance(data, list))
        self.assertTrue('Silva Image' in data)
        self.assertTrue('Silva Folder' in data)
        self.assertFalse('Silva Link' in data)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RESTAddablesTestCase))
    return suite
