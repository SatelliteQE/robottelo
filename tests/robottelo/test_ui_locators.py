"""Unit tests for :mod:`robottelo.ui.locators`."""
import unittest2
from robottelo.ui.locators.model import Locator, LocatorDict, By


class LocatorTestCase(unittest2.TestCase):
    def setUp(self):
        self.locators = LocatorDict(
            {
                "simple_locator": (By.XPATH, '//div'),
                "xpath_locator": Locator.XPATH('//div/%s'),
                "id_locator": Locator(By.ID, 'this_is_id_%s'),
            }
        )

    def test_add_new_locator_node_by_attr(self):
        self.locators.menu.home = Locator.XPATH('//nav//home')
        self.assertEqual(self.locators.menu.home._strategy, 'xpath')
        self.assertEqual(self.locators.menu.home._value, '//nav//home')

    def test_add_new_locator_node_by_key(self):
        self.locators['menu.contact'] = Locator.XPATH('//contact')
        self.assertEqual(self.locators['menu.contact']._strategy, 'xpath')
        self.assertEqual(self.locators['menu.contact']._value, '//contact')

    def test_add_new_locator_node_by_attr_using_tuple(self):
        self.locators.menu.home = (By.XPATH, '//nav//home')
        self.assertEqual(self.locators.menu.home._strategy, 'xpath')
        self.assertEqual(self.locators.menu.home._value, '//nav//home')

    def test_add_new_locator_node_by_key_using_tuple(self):
        self.locators['menu.contact'] = (By.XPATH, '//contact')
        self.assertEqual(self.locators['menu.contact']._strategy, 'xpath')
        self.assertEqual(self.locators['menu.contact']._value, '//contact')

    def test_root_node_is_empty(self):
        self.locators.menu.foo.bar.zaz.blarg = Locator.ID('buzz')
        self.assertEqual(self.locators.menu.foo.bar.zaz.blarg._value, 'buzz')
        self.assertIsNone(self.locators.menu.foo._value)
        self.assertIsNone(self.locators.menu.foo._strategy)

    def test_unpacking_as_tuple(self):
        strategy, value = self.locators.simple_locator
        self.assertEqual(strategy, By.XPATH)
        self.assertEqual(value, '//div')

    def test_function_argument_unpacking(self):
        def some_function(strategy, value):
            self.assertEqual(strategy, By.XPATH)
            self.assertEqual(value, '//div')
        some_function(*self.locators['simple_locator'])

    def test_different_access(self):
        self.locators.menu.foo.bar = Locator.ID('bar')
        self.assertEqual(self.locators.menu['foo']['bar'], Locator.ID('bar'))
        self.assertEqual(self.locators.menu['foo'].bar, Locator.ID('bar'))
        self.assertEqual(self.locators.menu.foo.bar, Locator.ID('bar'))
        self.assertEqual(self.locators['menu'].foo.bar, Locator.ID('bar'))
        self.assertEqual(self.locators['menu']['foo'].bar, Locator.ID('bar'))
        self.assertEqual(self.locators['menu']['foo']['bar'],
                         Locator.ID('bar'))
        self.assertEqual(self.locators['menu.foo.bar'], Locator.ID('bar'))

    def test_interpolation(self):
        new_loc = self.locators.xpath_locator % 'wow'
        self.assertEqual(new_loc._value, '//div/wow')
        self.assertEqual(new_loc._value, Locator.XPATH('//div/wow')._value)

    def test_getitem(self):
        root = LocatorDict()
        root.menu.home = Locator.XPATH('//div')
        # only 0 and 1 allowed
        self.assertEqual(root.menu.home[0], 'xpath')
        self.assertEqual(root.menu.home[1], '//div')
        # all new keys gets empty locator
        self.assertEqual(root.menu.home['empty_locator'], Locator())
        self.assertEqual(root.menu.home._strategy, 'xpath')
        # access by key also gets empty
        self.assertEqual(root['menu']['home']['empty'], Locator())
        # not allowed to access 3rd element
        with self.assertRaises(IndexError):
            root.menu.home[3]

    def test_requires_only_two_values(self):
        with self.assertRaises(ValueError):
            Locator(By.XPATH, '//div', 'aleatory')

    def test_inspect_members(self):
        root = LocatorDict()
        root.menu.home = Locator.XPATH('//div')
        root.menu.contact = Locator.ID('contact')
        root.menu.login = Locator.CLASS('login')
        self.assertEqual(
            sorted(dir(root.menu)),
            sorted(
                ['home', 'contact', 'login', '_store', '_value', '_strategy']
            )
        )

    def test_xpath_locator(self):
        self.assertEqual(Locator.XPATH('//div')._strategy, By.XPATH)

    def test_name_locator(self):
        self.assertEqual(Locator.NAME('foo')._strategy, By.NAME)

    def test_id_locator(self):
        self.assertEqual(Locator.ID('zaz')._strategy, By.ID)

    def test_tag_locator(self):
        self.assertEqual(Locator.TAG('form')._strategy, By.TAG_NAME)

    def test_link_text_locator(self):
        self.assertEqual(Locator.LINK_TEXT('hello')._strategy, By.LINK_TEXT)
        self.assertEqual(Locator.LINK_TEXT('hello', partial=True)._strategy,
                         By.PARTIAL_LINK_TEXT)

    def test_class_locator(self):
        self.assertEqual(Locator.CLASS('main')._strategy, By.CLASS_NAME)

    def test_css_locator(self):
        self.assertEqual(Locator.CSS('.main#a')._strategy, By.CSS_SELECTOR)

    def test_item_existance(self):
        root = LocatorDict()
        root.menu.home = Locator.XPATH('//div')
        self.assertTrue('home' in root.menu)
        self.assertTrue('menu' in root)
        self.assertFalse('baz' in root)
        self.assertFalse('foo' in root.menu)
        self.assertFalse('zaz' in root.menu.bla.arg)

    def test_init_with_named_locators(self):
        root = LocatorDict(
            menu=Locator.XPATH('//div'),
            logout=(By.ID, 'logout')
        )
        self.assertTrue('menu' in root)
        self.assertTrue('logout' in root)

    def test_init_with_dict_locators(self):
        root = LocatorDict({
            "menu": Locator.XPATH('//div'),
            "logout": (By.ID, 'logout')
        })
        self.assertTrue('menu' in root)
        self.assertTrue('logout' in root)

    def test_multi_level_locator(self):
        root = LocatorDict({
            "content_env.edit_description": (
                By.XPATH,
                ("//form[@bst-edit-textarea='environment.description']"
                 "//i[contains(@class,'fa-edit')]")),
            "content_env.edit_description_textarea.save": (
                By.XPATH,
                "//form[@bst-edit-textarea='environment.description']//button"
            ),
            "content_env.edit_description_textarea": (
                By.XPATH,
                ("//form[@bst-edit-textarea='environment.description']"
                 "/div/textarea")),
        })

        self.assertTrue(root['content_env']._is_root)
        self.assertFalse(root["content_env.edit_description"]._is_root)
        self.assertEqual(root["content_env.edit_description"][0], 'xpath')
        self.assertEqual(
            root["content_env.edit_description"][1],
            ("//form[@bst-edit-textarea='environment.description']"
             "//i[contains(@class,'fa-edit')]")
        )
        self.assertIn('save',
                      root["content_env.edit_description_textarea"].keys())
        self.assertEqual(
            root["content_env.edit_description_textarea.save"][1],
            "//form[@bst-edit-textarea='environment.description']//button"
        )

    def test_merge_locator_dicts(self):
        first = LocatorDict({
            "foo.bar": (By.XPATH, '//foo/bar'),
            "foo": (By.XPATH, '//foo'),
            "second.naz": (By.XPATH, '//second/naz')
        })
        second = Locator.XPATH('//foo/bar/blaz')
        second['zaz'] = ('xpath', '//zaz')
        self.assertIn('zaz', second.keys())

        self.assertTrue(first.second._is_root)
        first['second'] = second
        self.assertFalse(first.second._is_root)

        self.assertEqual(first.second[1], '//foo/bar/blaz')
        self.assertEqual(first['second.naz'][1], '//second/naz')
        self.assertEqual(first['second.zaz'][1], '//zaz')
