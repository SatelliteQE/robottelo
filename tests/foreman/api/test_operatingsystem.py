"""Unit tests for the ``operatingsystems`` paths.

References for the relevant paths can be found here:

* http://theforeman.org/api/apidoc/v2/operatingsystems.html
* http://theforeman.org/api/apidoc/v2/parameters.html

"""
import random
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import OPERATING_SYSTEMS
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase
from six.moves.http_client import NOT_FOUND


class OSParameterTestCase(APITestCase):
    """Tests for operating system parameters."""

    @tier1
    @run_only_on('sat')
    def test_bz_1114640(self):
        """@Test: Create a parameter for operating system 1.

        @Feature: Operating System Parameter

        @Assert: A parameter is created and can be read afterwards.
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
        name = gen_string('utf8')
        value = gen_string('utf8')
        os_param = entities.OperatingSystemParameter(
            name=name,
            operatingsystem=1,
            value=value,
        ).create()
        self.assertEqual(os_param.name, name)
        self.assertEqual(os_param.value, value)


class OSTestCase(APITestCase):
    """Tests for operating systems."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(OSTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    @run_only_on('sat')
    def test_positive_create_different_names(self):
        """@Test: Create operating system with valid name only

        @Feature: Operating System

        @Assert: Operating system entity is created and has proper name
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = entities.OperatingSystem(name=name).create()
                self.assertEqual(os.name, name)

    @tier1
    @run_only_on('sat')
    def test_positive_create_different_os_family(self):
        """@Test: Create operating system with every OS family possible

        @Feature: Operating System

        @Assert: Operating system entity is created and has proper OS family
        assigned
        """
        for os_family in OPERATING_SYSTEMS:
            with self.subTest(os_family):
                os = entities.OperatingSystem(family=os_family).create()
                self.assertEqual(os.family, os_family)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_minor(self):
        """@Test: Create operating system with minor version

        @Feature: Operating System

        @Assert: Operating system entity is created and has proper minor
        version
        """
        minor_version = gen_string('numeric')
        os = entities.OperatingSystem(minor=minor_version).create()
        self.assertEqual(os.minor, minor_version)

    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1230902)
    def test_create_with_minor_1230902(self):
        """@Test: Create an operating system with an integer minor version.

        @Feature: Operating System

        @Assert: The minor version can be read back as a string.
        """
        minor = int(gen_string('numeric', random.randint(1, 16)))
        operating_sys = entities.OperatingSystem(minor=minor).create()
        self.assertEqual(operating_sys.minor, str(minor))

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_description(self):
        """@Test: Create operating system with description

        @Feature: Operating System

        @Assert: Operating system entity is created and has proper description
        """
        name = gen_string('utf8')
        for desc in valid_data_list():
            with self.subTest(desc):
                os = entities.OperatingSystem(
                    name=name, description=desc).create()
                self.assertEqual(os.name, name)
                self.assertEqual(os.description, desc)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_hash(self):
        """@Test: Create operating system with valid password hash option

        @Feature: Operating System

        @Assert: Operating system entity is created and has proper password
        hash type
        """
        for pass_hash in ['MD5', 'SHA256', 'SHA512']:
            with self.subTest(pass_hash):
                os = entities.OperatingSystem(password_hash=pass_hash).create()
                self.assertEqual(os.password_hash, pass_hash)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_arch(self):
        """@Test: Create an operating system that points at an architecture.

        @Feature: Operating System

        @Assert: The operating system is created and points at the given
        architecture.
        """
        arch = entities.Architecture().create()
        operating_sys = entities.OperatingSystem(architecture=[arch]).create()
        self.assertEqual(len(operating_sys.architecture), 1)
        self.assertEqual(operating_sys.architecture[0].id, arch.id)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_multiple_archs(self):
        """@Test: Create an operating system that points at multiple different
        architectures.

        @Feature: Operating System

        @Assert: The operating system is created and points at the expected
        architectures.
        """
        amount = range(random.randint(3, 5))
        archs = [entities.Architecture().create() for _ in amount]
        operating_sys = entities.OperatingSystem(architecture=archs).create()
        self.assertEqual(len(operating_sys.architecture), len(amount))
        self.assertEqual(
            set([arch.id for arch in operating_sys.architecture]),
            set([arch.id for arch in archs])
        )

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_ptable(self):
        """@Test: Create an operating system that points at a partition table.

        @Feature: Operating System

        @Assert: The operating system is created and points at the given
        partition table.
        """
        ptable = entities.PartitionTable().create()
        operating_sys = entities.OperatingSystem(ptable=[ptable]).create()
        self.assertEqual(len(operating_sys.ptable), 1)
        self.assertEqual(operating_sys.ptable[0].id, ptable.id)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_multiple_ptables(self):
        """@Test: Create an operating system that points at multiple different
        partition tables.

        @Feature: Operating System

        @Assert: The operating system is created and points at the expected
        partition tables.
        """
        amount = range(random.randint(3, 5))
        ptables = [entities.PartitionTable().create() for _ in amount]
        operating_sys = entities.OperatingSystem(ptable=ptables).create()
        self.assertEqual(len(operating_sys.ptable), len(amount))
        self.assertEqual(
            set([ptable.id for ptable in operating_sys.ptable]),
            set([ptable.id for ptable in ptables])
        )

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_media(self):
        """@Test: Create an operating system that points at a media.

        @Feature: Operating System

        @Assert: The operating system is created and points at the given media.
        """
        medium = entities.Media(organization=[self.org]).create()
        operating_sys = entities.OperatingSystem(medium=[medium]).create()
        self.assertEqual(len(operating_sys.medium), 1)
        self.assertEqual(operating_sys.medium[0].id, medium.id)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_template(self):
        """@Test: Create an operating system that points at a config template.

        @Feature: Operating System

        @Assert: The operating system is created and points at the expected
        config template.
        """
        template = entities.ConfigTemplate(organization=[self.org]).create()
        operating_sys = entities.OperatingSystem(
            config_template=[template]).create()
        self.assertEqual(len(operating_sys.config_template), 1)
        self.assertEqual(operating_sys.config_template[0].id, template.id)

    @tier1
    @run_only_on('sat')
    def test_negative_create_different_names(self):
        """@Test: Try to create operating system entity providing an invalid
        name

        @Feature: Operating System

        @Assert: Operating system entity is not created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.OperatingSystem(name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_os_family(self):
        """@Test: Try to create operating system entity providing an invalid
        operating system family

        @Feature: Operating System

        @Assert: Operating system entity is not created
        """
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(family='NON_EXISTENT_OS').create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_too_long_description(self):
        """@Test: Try to create operating system entity providing too long
        description value

        @Feature: Operating System

        @Assert: Operating system entity is not created
        """
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(
                description=gen_string('alphanumeric', 256)).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_wrong_major_version(self):
        """@Test: Try to create operating system entity providing incorrect
        major version value (More than 5 characters, empty value, negative
        number)

        @Feature: Operating System

        @Assert: Operating system entity is not created
        """
        for major_version in gen_string('numeric', 6), '', '-6':
            with self.subTest(major_version):
                with self.assertRaises(HTTPError):
                    entities.OperatingSystem(major=major_version).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_wrong_minor_version(self):
        """@Test: Try to create operating system entity providing incorrect
        minor version value (More than 16 characters and negative number)

        @Feature: Operating System

        @Assert: Operating system entity is not created
        """
        for minor_version in gen_string('numeric', 17), '-5':
            with self.subTest(minor_version):
                with self.assertRaises(HTTPError):
                    entities.OperatingSystem(minor=minor_version).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_wrong_hash(self):
        """@Test: Try to create operating system entity providing invalid
        password hash value

        @Feature: Operating System

        @Assert: Operating system entity is not created
        """
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(password_hash='INVALID_HASH').create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_same_name_and_version(self):
        """@Test: Create operating system providing valid name and major
        version. Then try to create operating system using the same name and
        version

        @Feature: Operating System

        @Assert: Second operating system entity is not created
        """
        os = entities.OperatingSystem().create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(name=os.name, major=os.major).create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_different_names(self):
        """@Test: Create operating system entity providing the initial name,
        then update its name to another valid name.

        @Feature: Operating System

        @Assert: Operating system entity is created and updated properly
        """
        os = entities.OperatingSystem().create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                os = entities.OperatingSystem(
                    id=os.id, name=new_name).update(['name'])
                self.assertEqual(os.name, new_name)

    @tier1
    @run_only_on('sat')
    def test_positive_update_description(self):
        """@Test: Create operating entity providing the initial description,
        then update that description to another valid one.

        @Feature: Operating System

        @Assert: Operating system entity is created and updated properly
        """
        os = entities.OperatingSystem(description=gen_string('utf8')).create()
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                os = entities.OperatingSystem(
                    id=os.id, description=new_desc).update(['description'])
                self.assertEqual(os.description, new_desc)

    @tier1
    @run_only_on('sat')
    def test_positive_update_major_version(self):
        """@Test: Create operating entity providing the initial major version,
        then update that version to another valid one.

        @Feature: Operating System

        @Assert: Operating system entity is created and updated properly
        """
        os = entities.OperatingSystem().create()
        new_major_version = gen_string('numeric', 5)
        os = entities.OperatingSystem(
            id=os.id, major=new_major_version).update(['major'])
        self.assertEqual(os.major, new_major_version)

    @tier1
    @run_only_on('sat')
    def test_positive_update_minor_version(self):
        """@Test: Create operating entity providing the initial minor version,
        then update that version to another valid one.

        @Feature: Operating System

        @Assert: Operating system entity is created and updated properly
        """
        os = entities.OperatingSystem(minor=gen_string('numeric')).create()
        new_minor_version = gen_string('numeric')
        os = entities.OperatingSystem(
            id=os.id, minor=new_minor_version).update(['minor'])
        self.assertEqual(os.minor, new_minor_version)

    @tier1
    @run_only_on('sat')
    def test_positive_update_os_family(self):
        """@Test: Create operating entity providing the initial os family, then
        update that family to another valid one from the list.

        @Feature: Operating System

        @Assert: Operating system entity is created and updated properly
        """
        os = entities.OperatingSystem(family=OPERATING_SYSTEMS[0]).create()
        new_os_family = OPERATING_SYSTEMS[
            random.randint(1, len(OPERATING_SYSTEMS)-1)]
        os = entities.OperatingSystem(
            id=os.id, family=new_os_family).update(['family'])
        self.assertEqual(os.family, new_os_family)

    @tier1
    @run_only_on('sat')
    def test_positive_update_with_arch(self):
        """@Test: Create an operating system that points at an architecture and
        then update it to point to another architecture

        @Feature: Operating System

        @Assert: The operating system is updated and points at the expected
        architecture.
        """
        arch_1 = entities.Architecture().create()
        arch_2 = entities.Architecture().create()
        os = entities.OperatingSystem(architecture=[arch_1]).create()
        self.assertEqual(len(os.architecture), 1)
        self.assertEqual(os.architecture[0].id, arch_1.id)
        os = entities.OperatingSystem(
            id=os.id, architecture=[arch_2]).update(['architecture'])
        self.assertEqual(len(os.architecture), 1)
        self.assertEqual(os.architecture[0].id, arch_2.id)

    @tier1
    @run_only_on('sat')
    def test_positive_update_with_ptable(self):
        """@Test: Create an operating system that points at partition table and
        then update it to point to another partition table

        @Feature: Operating System

        @Assert: The operating system is updated and points at the expected
        partition table.
        """
        ptable_1 = entities.PartitionTable().create()
        ptable_2 = entities.PartitionTable().create()
        os = entities.OperatingSystem(ptable=[ptable_1]).create()
        self.assertEqual(len(os.ptable), 1)
        self.assertEqual(os.ptable[0].id, ptable_1.id)
        os = entities.OperatingSystem(
            id=os.id, ptable=[ptable_2]).update(['ptable'])
        self.assertEqual(len(os.ptable), 1)
        self.assertEqual(os.ptable[0].id, ptable_2.id)

    @tier1
    @run_only_on('sat')
    def test_positive_update_with_media(self):
        """@Test: Create an operating system that points at media entity and
        then update it to point to another media

        @Feature: Operating System

        @Assert: The operating system is updated and points at the expected
        media.
        """
        media_1 = entities.Media(organization=[self.org]).create()
        media_2 = entities.Media(organization=[self.org]).create()
        os = entities.OperatingSystem(medium=[media_1]).create()
        self.assertEqual(len(os.medium), 1)
        self.assertEqual(os.medium[0].id, media_1.id)
        os = entities.OperatingSystem(
            id=os.id, medium=[media_2]).update(['medium'])
        self.assertEqual(len(os.medium), 1)
        self.assertEqual(os.medium[0].id, media_2.id)

    @tier1
    @run_only_on('sat')
    def test_positive_update_with_multiple_medias(self):
        """@Test: Create an operating system that points at media entity and
        then update it to point to another multiple different medias.

        @Feature: Operating System

        @Assert: The operating system is updated and points at the expected
        medias.
        """
        initial_media = entities.Media(organization=[self.org]).create()
        os = entities.OperatingSystem(medium=[initial_media]).create()
        self.assertEqual(len(os.medium), 1)
        self.assertEqual(os.medium[0].id, initial_media.id)
        amount = range(random.randint(3, 5))
        medias = [entities.Media().create() for _ in amount]
        os = entities.OperatingSystem(
            id=os.id, medium=medias).update(['medium'])
        self.assertEqual(len(os.medium), len(amount))
        self.assertEqual(
            set([medium.id for medium in os.medium]),
            set([medium.id for medium in medias])
        )

    @tier1
    @run_only_on('sat')
    def test_positive_update_with_template(self):
        """@Test: Create an operating system that points at config template and
        then update it to point to another template

        @Feature: Operating System

        @Assert: The operating system is updated and points at the expected
        config template.
        """
        template_1 = entities.ConfigTemplate(organization=[self.org]).create()
        template_2 = entities.ConfigTemplate(organization=[self.org]).create()
        os = entities.OperatingSystem(config_template=[template_1]).create()
        self.assertEqual(len(os.config_template), 1)
        self.assertEqual(os.config_template[0].id, template_1.id)
        os = entities.OperatingSystem(
            id=os.id, config_template=[template_2]).update(['config_template'])
        self.assertEqual(len(os.config_template), 1)
        self.assertEqual(os.config_template[0].id, template_2.id)

    @tier1
    @run_only_on('sat')
    def test_negative_update_different_names(self):
        """@Test: Create operating system entity providing the initial name,
        then update its name to invalid one.

        @Feature: Operating System

        @Assert: Operating system entity is not updated
        """
        os = entities.OperatingSystem().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    os = entities.OperatingSystem(
                        id=os.id, name=new_name).update(['name'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_major_version(self):
        """@Test: Create operating entity providing the initial major version,
        then update that version to invalid one.

        @Feature: Operating System

        @Assert: Operating system entity is not updated
        """
        os = entities.OperatingSystem().create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(id=os.id, major='-20').update(['major'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_minor_version(self):
        """@Test: Create operating entity providing the initial minor version,
        then update that version to invalid one.

        @Feature: Operating System

        @Assert: Operating system entity is not updated
        """
        os = entities.OperatingSystem(minor=gen_string('numeric')).create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(
                id=os.id, minor='INVALID_VERSION').update(['minor'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_os_family(self):
        """@Test: Create operating entity providing the initial os family, then
        update that family to invalid one.

        @Feature: Operating System

        @Assert: Operating system entity is not updated
        """
        os = entities.OperatingSystem(family=OPERATING_SYSTEMS[0]).create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(
                id=os.id, family='NON_EXISTENT_OS').update(['family'])

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """@Test: Create new operating system entity and then delete it.

        @Feature: Operating System

        @Assert: Operating System entity is deleted successfully
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = entities.OperatingSystem(name=name).create()
                os.delete()
                with self.assertRaises(HTTPError):
                    os.read()
