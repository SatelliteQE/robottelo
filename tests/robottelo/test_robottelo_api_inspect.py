"""Unit tests for module ``robottelo.api.inspect``."""
import unittest

from mock import patch
from robottelo.api import inspect


MOCK_API_DOC = {
    'resources': {
        'aresource': {
            'methods': [{
                'name': 'create',
                'apis': ['/an/api/path'],
                'params': [{'name': 'param1'}],
            }],
        }
    },
}

RESULT_FOR_MOCK_API_DOC = {
    'aresource': {
        'apis': ['/an/api/path'],
        'params': [{'name': 'param1'}]
    }
}


class ResourceCreateInfoTestCase(unittest.TestCase):
    """Tests for function ``get_resource_create_info``."""

    @patch('robottelo.api.inspect.get_api_doc')
    def test_calls_get_api_doc(self, _get_api_doc):
        """Call ``get_api_doc`` if no ``api_doc`` is provided"""
        _get_api_doc.return_value = {
            'resources': {},
        }

        info = inspect.get_resource_create_info()

        _get_api_doc.assert_called_once()
        self.assertEqual(info, {})

    @patch('robottelo.api.inspect.get_api_doc')
    def test_get_and_parses_api_doc_info(self, _get_api_doc):
        """Get and parse api doc information and returns a list of resources"""
        _get_api_doc.return_value = MOCK_API_DOC

        info = inspect.get_resource_create_info()

        _get_api_doc.assert_called_once_with()
        self.assertEqual(info, RESULT_FOR_MOCK_API_DOC)

    def test_parses_api_doc_info(self):
        """Parse api doc information and returns a list of resources"""
        info = inspect.get_resource_create_info(MOCK_API_DOC)

        self.assertEqual(info, RESULT_FOR_MOCK_API_DOC)
