"""Unit tests for the ``operatingsystems`` paths.

References for the relevant paths can be found here:

* http://theforeman.org/api/apidoc/v2/operatingsystems.html
* http://theforeman.org/api/apidoc/v2/parameters.html

"""
from fauxfactory import gen_integer, gen_utf8
from httplib import NOT_FOUND
from nailgun import entities
from robottelo.common.decorators import run_only_on
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


@run_only_on('sat')
class OSParameterTestCase(APITestCase):
    """Tests for operating system parameters."""

    def test_bz_1114640(self):
        """@Test: Create a parameter for operating system 1.

        @Assert: A parameter is created and can be read afterwards.

        @Feature: OperatingSystemParameter

        """
        # Check whether OS 1 exists.
        if (entities.OperatingSystem(id=1).read_raw().status_code == NOT_FOUND
                and entities.OperatingSystem().create_json()['id'] != 1):
            self.skipTest(
                'Cannot execute test, as operating system 1 is not available.'
            )

        # Create and read a parameter for operating system 1. The purpose of
        # this test is to make sure an HTTP 422 is not returned, but we're also
        # going to verify the name and value of the parameter, just for good
        # measure.
        name = gen_utf8(20)
        value = gen_utf8(20)
        osp_id = entities.OperatingSystemParameter(
            name=name,
            operatingsystem=1,
            value=value,
        ).create_json()['id']
        attrs = entities.OperatingSystemParameter(
            id=osp_id,
            operatingsystem=1,
        ).read_json()
        self.assertEqual(attrs['name'], name)
        self.assertEqual(attrs['value'], value)


@run_only_on('sat')
class OSTestCase(APITestCase):
    """Tests for operating systems."""

    def test_point_to_arch(self):
        """@Test: Create an operating system that points at an architecture.

        @Assert: The operating system is created and points at the given
        architecture.

        @Feature: OperatingSystem

        """
        arch_id = entities.Architecture().create_json()['id']
        os_id = entities.OperatingSystem(
            architecture=[arch_id]
        ).create_json()['id']
        attrs = entities.OperatingSystem(id=os_id).read_json()
        self.assertEqual(len(attrs['architectures']), 1)
        self.assertEqual(attrs['architectures'][0]['id'], arch_id)

    def test_point_to_ptable(self):
        """@Test: Create an operating system that points at a partition table.

        @Assert: The operating system is created and points at the given
        partition table.

        @Feature: OperatingSystem

        """
        ptable_id = entities.PartitionTable().create_json()['id']
        os_id = entities.OperatingSystem(
            ptable=[ptable_id]
        ).create_json()['id']
        attrs = entities.OperatingSystem(id=os_id).read_json()
        self.assertEqual(len(attrs['ptables']), 1)
        self.assertEqual(attrs['ptables'][0]['id'], ptable_id)

    def test_create_with_minor(self):
        """@Test: Create an operating system with an integer minor version.

        @Assert: The minor version can be read back as a string.

        @Feature: OperatingSystem

        Targets BZ 1125003.

        """
        minor = gen_integer(0, 9999999999999999)  # max len: 16 chars
        os_id = entities.OperatingSystem(minor=minor).create_json()['id']
        self.assertEqual(
            entities.OperatingSystem(id=os_id).read().minor,
            str(minor),
        )
