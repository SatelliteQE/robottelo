"""Unit tests for the ``api/v2/operatingsystems/:id/parameters`` paths.

A reference for the relevant paths can be found here:
http://theforeman.org/api/apidoc/v2/parameters.html

"""
from robottelo import entities
from robottelo.common.decorators import run_only_on
from unittest import TestCase
# (too many public methods) pylint: disable=R0904


@run_only_on('sat')
class OSParameterTestCase(TestCase):
    """Tests for the ``api/v2/operatingsystems/:id/parameters`` paths."""
    def test_bz_1114640(self):
        """@Test: Create a parameter for operating system 1.

        @Assert: A parameter is created and can be read afterwards.

        """
        # Check whether OS 1 exists. Do not catch
        # requests.exceptions.HTTPError, as doing so destroys useful stack
        # trace information.
        entities.OperatingSystem(id=1).read()

        # Create a param for OS 1 and read the param back.
        osp_attrs = entities.OperatingSystemParameter(1).create()
        osp = entities.OperatingSystemParameter(1, id=osp_attrs['id']).read()

        # The main point of this test is "does create() return an HTTP 422?"
        # These are here just for good measure.
        self.assertEqual(osp_attrs['name'], osp.name)
        self.assertEqual(osp_attrs['value'], osp.value)
