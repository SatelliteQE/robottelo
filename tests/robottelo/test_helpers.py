import unittest

from robottelo.common.helpers import (
    generate_name, generate_email_address, valid_names_list, valid_data_list,
    invalid_names_list, generate_ipaddr, generate_mac, generate_string,
    generate_strings_list)


class GenerateNameTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if generate name returns a unicode string"""
        self.assertIsInstance(generate_name(), unicode)


class GenerateEmailAddressTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if generate email address returns a unicode string"""
        self.assertIsInstance(generate_email_address(), unicode)


class ValidNamesListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if valid names list returns a unicode string"""
        for name in valid_names_list():
            self.assertIsInstance(name, unicode)


class ValidDataListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if valid data list returns a unicode string"""
        for data in valid_data_list():
            self.assertIsInstance(data, unicode)


class InvalidNamesListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if invalid names list returns a unicode string"""
        for name in invalid_names_list():
            self.assertIsInstance(name, unicode)


class GenerateIPAddrTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if generate ipaddr returns a unicode string"""
        self.assertIsInstance(generate_ipaddr(), unicode)
        self.assertIsInstance(generate_ipaddr(ip3=True), unicode)


class GenerateMACTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if generate mac returns a unicode string"""
        self.assertIsInstance(generate_mac(), unicode)


class GenerateStringTestCase(unittest.TestCase):
    def test_alphanumeric_return_type(self):
        """Tests if generate alphanumeric string returns a unicode string"""
        self.assertIsInstance(generate_string('alphanumeric', 8), unicode)

    def test_alpha_return_type(self):
        """Tests if generate alpha string returns a unicode string"""
        self.assertIsInstance(generate_string('alpha', 8), unicode)

    def test_numeric_return_type(self):
        """Tests if generate numeric string returns a unicode string"""
        self.assertIsInstance(generate_string('numeric', 8), unicode)

    def test_latin1_return_type(self):
        """Tests if generate latin1 string returns a unicode string"""
        self.assertIsInstance(generate_string('latin1', 8), unicode)

    def test_utf8_return_type(self):
        """Tests if generate utf-8 string returns a unicode string"""
        self.assertIsInstance(generate_string('utf8', 8), unicode)

    def test_html_return_type(self):
        """Tests if generate html string returns a unicode string"""
        self.assertIsInstance(generate_string('html', 8), unicode)


class GenerateStringListTestCase(unittest.TestCase):
    def test_return_type(self):
        """Tests if generate string list returns a unicode string"""
        for string in generate_strings_list():
            self.assertIsInstance(string, unicode)
