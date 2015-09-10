"""Unit tests for the ``operatingsystems`` paths.

References for the relevant paths can be found here:

* http://theforeman.org/api/apidoc/v2/operatingsystems.html
* http://theforeman.org/api/apidoc/v2/parameters.html

"""
from fauxfactory import gen_integer, gen_utf8
from httplib import NOT_FOUND
from nailgun import entities
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.test import APITestCase


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
                and entities.OperatingSystem().create().id != 1):
            self.skipTest(
                'Cannot execute test, as operating system 1 is not available.'
            )

        # Create and read a parameter for operating system 1. The purpose of
        # this test is to make sure an HTTP 422 is not returned, but we're also
        # going to verify the name and value of the parameter, just for good
        # measure.
        name = gen_utf8(20)
        value = gen_utf8(20)
        os_param = entities.OperatingSystemParameter(
            name=name,
            operatingsystem=1,
            value=value,
        ).create()
        self.assertEqual(os_param.name, name)
        self.assertEqual(os_param.value, value)


@run_only_on('sat')
class OSTestCase(APITestCase):
    """Tests for operating systems."""

    def test_point_to_arch(self):
        """@Test: Create an operating system that points at an architecture.

        @Assert: The operating system is created and points at the given
        architecture.

        @Feature: OperatingSystem

        """
        arch = entities.Architecture().create()
        operating_sys = entities.OperatingSystem(architecture=[arch]).create()
        self.assertEqual(len(operating_sys.architecture), 1)
        self.assertEqual(operating_sys.architecture[0].id, arch.id)

    def test_point_to_ptable(self):
        """@Test: Create an operating system that points at a partition table.

        @Assert: The operating system is created and points at the given
        partition table.

        @Feature: OperatingSystem

        """
        ptable = entities.PartitionTable().create()
        operating_sys = entities.OperatingSystem(ptable=[ptable]).create()
        self.assertEqual(len(operating_sys.ptable), 1)
        self.assertEqual(operating_sys.ptable[0].id, ptable.id)

    @skip_if_bug_open('bugzilla', 1230902)
    def test_create_with_minor(self):
        """@Test: Create an operating system with an integer minor version.

        @Assert: The minor version can be read back as a string.

        @Feature: OperatingSystem

        Targets BZ 1125003.

        """
        minor = gen_integer(0, 9999999999999999)  # max len: 16 chars
        operating_sys = entities.OperatingSystem(minor=minor).create()
        self.assertEqual(operating_sys.minor, str(minor))
