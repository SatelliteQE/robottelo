"""Unit tests for the ``operatingsystems`` paths.

References for the relevant paths can be found on your Satellite:

* http://<sat6>/apidoc/v2/operatingsystems.html
* http://<sat6>/apidoc/v2/parameters.html


:Requirement: Operatingsystem

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import OPERATING_SYSTEMS
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import (
    bz_bug_is_open,
    skip_if_bug_open,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import APITestCase
from six.moves.http_client import NOT_FOUND


class OperatingSystemParameterTestCase(APITestCase):
    """Tests for operating system parameters."""

    @tier1
    @upgrade
    def test_verify_bugzilla_1114640(self):
        """Create a parameter for operating system 1.

        :id: e817ae43-226c-44e3-b559-62b8d394047b

        :expectedresults: A parameter is created and can be read afterwards.

        :CaseImportance: Critical
        """
        # Check whether OS 1 exists.
        os1 = entities.OperatingSystem(id=1).read_raw()
        if (os1.status_code == NOT_FOUND and
                entities.OperatingSystem().create().id != 1):
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


class OperatingSystemTestCase(APITestCase):
    """Tests for operating systems."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(OperatingSystemTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create operating system with valid name only

        :id: e95707bf-3344-4d85-866f-4642a8f66cff

        :expectedresults: Operating system entity is created and has proper
            name

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = entities.OperatingSystem(name=name).create()
                self.assertEqual(os.name, name)

    @tier1
    def test_positive_create_with_os_family(self):
        """Create operating system with every OS family possible

        :id: 6ad32d22-53cc-4bab-ac10-f466f75d7cc6

        :expectedresults: Operating system entity is created and has proper OS
            family assigned

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        for os_family in OPERATING_SYSTEMS:
            with self.subTest(os_family):
                if bz_bug_is_open(1709683):
                    if os_family == 'Debian':
                        continue
                os = entities.OperatingSystem(family=os_family).create()
                self.assertEqual(os.family, os_family)

    @tier1
    def test_positive_create_with_minor_version(self):
        """Create operating system with minor version

        :id: fc2e36ca-eb5c-440b-957e-390cd9820945

        :expectedresults: Operating system entity is created and has proper
            minor version

        :CaseImportance: Critical
        """
        minor_version = gen_string('numeric')
        os = entities.OperatingSystem(minor=minor_version).create()
        self.assertEqual(os.minor, minor_version)

    @tier1
    @skip_if_bug_open('bugzilla', 1230902)
    def test_verify_bugzilla_1230902(self):
        """Create an operating system with an integer minor version.

        :id: b45e0b94-62f7-45ff-a19e-83c7a0f51339

        :expectedresults: The minor version can be read back as a string.

        :CaseImportance: Critical
        """
        minor = int(gen_string('numeric', random.randint(1, 16)))
        operating_sys = entities.OperatingSystem(minor=minor).create()
        self.assertEqual(operating_sys.minor, str(minor))

    @tier1
    def test_positive_create_with_description(self):
        """Create operating system with description

        :id: 980e6411-da11-4fec-ae46-47722367ae40

        :expectedresults: Operating system entity is created and has proper
            description

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        for desc in valid_data_list():
            with self.subTest(desc):
                os = entities.OperatingSystem(
                    name=name, description=desc).create()
                self.assertEqual(os.name, name)
                self.assertEqual(os.description, desc)

    @tier1
    def test_positive_create_with_password_hash(self):
        """Create operating system with valid password hash option

        :id: 00830e71-b414-41ab-bc8f-03fd2fbd5a84

        :expectedresults: Operating system entity is created and has proper
            password hash type

        :CaseImportance: Critical
        """
        for pass_hash in ['SHA256', 'SHA512']:
            with self.subTest(pass_hash):
                os = entities.OperatingSystem(password_hash=pass_hash).create()
                self.assertEqual(os.password_hash, pass_hash)

    @tier2
    def test_positive_create_with_arch(self):
        """Create an operating system that points at an architecture.

        :id: 6a3f7183-b0bf-4834-8c69-a49fe8d7ee5a

        :expectedresults: The operating system is created and points at the
            given architecture.

        :CaseLevel: Integration
        """
        arch = entities.Architecture().create()
        operating_sys = entities.OperatingSystem(architecture=[arch]).create()
        self.assertEqual(len(operating_sys.architecture), 1)
        self.assertEqual(operating_sys.architecture[0].id, arch.id)

    @tier2
    def test_positive_create_with_archs(self):
        """Create an operating system that points at multiple different
        architectures.

        :id: afd26c6a-bf54-4883-baa5-95f263e6fb36

        :expectedresults: The operating system is created and points at the
            expected architectures.

        :CaseLevel: Integration
        """
        amount = range(random.randint(3, 5))
        archs = [entities.Architecture().create() for _ in amount]
        operating_sys = entities.OperatingSystem(architecture=archs).create()
        self.assertEqual(len(operating_sys.architecture), len(amount))
        self.assertEqual(
            set([arch.id for arch in operating_sys.architecture]),
            set([arch.id for arch in archs])
        )

    @tier2
    def test_positive_create_with_ptable(self):
        """Create an operating system that points at a partition table.

        :id: bef37ff9-d8fa-4518-9073-0518aa9f9a42

        :expectedresults: The operating system is created and points at the
            given partition table.

        :CaseLevel: Integration
        """
        ptable = entities.PartitionTable().create()
        operating_sys = entities.OperatingSystem(ptable=[ptable]).create()
        self.assertEqual(len(operating_sys.ptable), 1)
        self.assertEqual(operating_sys.ptable[0].id, ptable.id)

    @tier2
    def test_positive_create_with_ptables(self):
        """Create an operating system that points at multiple different
        partition tables.

        :id: ed48a279-a222-45ce-81e4-72ae9422482a

        :expectedresults: The operating system is created and points at the
            expected partition tables.

        :CaseLevel: Integration
        """
        amount = range(random.randint(3, 5))
        ptables = [entities.PartitionTable().create() for _ in amount]
        operating_sys = entities.OperatingSystem(ptable=ptables).create()
        self.assertEqual(len(operating_sys.ptable), len(amount))
        self.assertEqual(
            set([ptable.id for ptable in operating_sys.ptable]),
            set([ptable.id for ptable in ptables])
        )

    @tier2
    def test_positive_create_with_media(self):
        """Create an operating system that points at a media.

        :id: 56fadee4-c676-48b6-a2db-e6fef9d2a575

        :expectedresults: The operating system is created and points at the
            given media.

        :CaseLevel: Integration
        """
        medium = entities.Media(organization=[self.org]).create()
        operating_sys = entities.OperatingSystem(medium=[medium]).create()
        self.assertEqual(len(operating_sys.medium), 1)
        self.assertEqual(operating_sys.medium[0].id, medium.id)

    @tier2
    def test_positive_create_with_template(self):
        """Create an operating system that points at a config template.

        :id: df73ecba-5a1c-4201-9c2f-b2e03e8fec25

        :expectedresults: The operating system is created and points at the
            expected config template.

        :CaseLevel: Integration
        """
        template = entities.ConfigTemplate(organization=[self.org]).create()
        operating_sys = entities.OperatingSystem(
            config_template=[template]).create()
        self.assertEqual(len(operating_sys.config_template), 1)
        self.assertEqual(operating_sys.config_template[0].id, template.id)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create operating system entity providing an invalid
        name

        :id: cd4286fd-7128-4385-9c8d-ef979c22ee38

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.OperatingSystem(name=name).create()

    @tier1
    def test_negative_create_with_invalid_os_family(self):
        """Try to create operating system entity providing an invalid
        operating system family

        :id: 205a433d-750b-4b06-9fd4-274303780d6d

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(family='NON_EXISTENT_OS').create()

    @tier1
    @skip_if_bug_open('bugzilla', 1328935)
    def test_negative_create_with_too_long_description(self):
        """Try to create operating system entity providing too long
        description value

        :id: fe5fc36a-5994-4d8a-91f6-0425765b8c39

        :expectedresults: Operating system entity is not created

        :BZ: 1328935

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(
                description=gen_string('alphanumeric', 256)).create()

    @tier1
    def test_negative_create_with_invalid_major_version(self):
        """Try to create operating system entity providing incorrect
        major version value (More than 5 characters, empty value, negative
        number)

        :id: f2646bc2-d639-4079-bdcb-ff76679f1457

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        for major_version in gen_string('numeric', 6), '', '-6':
            with self.subTest(major_version):
                with self.assertRaises(HTTPError):
                    entities.OperatingSystem(major=major_version).create()

    @tier1
    def test_negative_create_with_invalid_minor_version(self):
        """Try to create operating system entity providing incorrect
        minor version value (More than 16 characters and negative number)

        :id: dec4b456-153c-4a66-8b8e-b12ac7800e51

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        for minor_version in gen_string('numeric', 17), '-5':
            with self.subTest(minor_version):
                with self.assertRaises(HTTPError):
                    entities.OperatingSystem(minor=minor_version).create()

    @tier1
    def test_negative_create_with_invalid_password_hash(self):
        """Try to create operating system entity providing invalid
        password hash value

        :id: 9cfcb6d4-0601-4fc7-bd1e-8b8327129a69

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(password_hash='INVALID_HASH').create()

    @tier1
    def test_negative_create_with_same_name_and_version(self):
        """Create operating system providing valid name and major
        version. Then try to create operating system using the same name and
        version

        :id: 3f2ca323-7789-4d2b-bf21-2454317147ff

        :expectedresults: Second operating system entity is not created

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem().create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(name=os.name, major=os.major).create()

    @tier1
    def test_positive_update_name(self):
        """Create operating system entity providing the initial name,
        then update its name to another valid name.

        :id: 2898e16a-865a-4de6-b2a5-bb0934fc2b76

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem().create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                os = entities.OperatingSystem(
                    id=os.id, name=new_name).update(['name'])
                self.assertEqual(os.name, new_name)

    @tier1
    def test_positive_update_description(self):
        """Create operating entity providing the initial description,
        then update that description to another valid one.

        :id: c809700a-b6ab-4651-9bd0-d0d9bd6a47dd

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem(description=gen_string('utf8')).create()
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                os = entities.OperatingSystem(
                    id=os.id, description=new_desc).update(['description'])
                self.assertEqual(os.description, new_desc)

    @tier1
    def test_positive_update_major_version(self):
        """Create operating entity providing the initial major version,
        then update that version to another valid one.

        :id: e57fd4a3-f0ae-49fb-bd84-9a6ec606a2a2

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem().create()
        new_major_version = gen_string('numeric', 5)
        os = entities.OperatingSystem(
            id=os.id, major=new_major_version).update(['major'])
        self.assertEqual(os.major, new_major_version)

    @tier1
    def test_positive_update_minor_version(self):
        """Create operating entity providing the initial minor version,
        then update that version to another valid one.

        :id: ca36f7cf-4487-4743-be06-52c5f47ffe71

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem(minor=gen_string('numeric')).create()
        new_minor_version = gen_string('numeric')
        os = entities.OperatingSystem(
            id=os.id, minor=new_minor_version).update(['minor'])
        self.assertEqual(os.minor, new_minor_version)

    @tier1
    def test_positive_update_os_family(self):
        """Create operating entity providing the initial os family, then
        update that family to another valid one from the list.

        :id: 3d1f8fdc-d2de-4277-a0ba-07228a2fae82

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem(family=OPERATING_SYSTEMS[0]).create()
        new_os_family = OPERATING_SYSTEMS[
            random.randint(1, len(OPERATING_SYSTEMS)-1)]
        os = entities.OperatingSystem(
            id=os.id, family=new_os_family).update(['family'])
        self.assertEqual(os.family, new_os_family)

    @tier2
    @upgrade
    def test_positive_update_arch(self):
        """Create an operating system that points at an architecture and
        then update it to point to another architecture

        :id: ad69b4a3-6371-4516-b5ce-f6298edf35b3

        :expectedresults: The operating system is updated and points at the
            expected architecture.

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_ptable(self):
        """Create an operating system that points at partition table and
        then update it to point to another partition table

        :id: 0dde5372-4b90-4c83-b497-31e94065adab

        :expectedresults: The operating system is updated and points at the
            expected partition table.

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_media(self):
        """Create an operating system that points at media entity and
        then update it to point to another media

        :id: 18b5f6b5-52ab-4722-8412-f0de85ad20fe

        :expectedresults: The operating system is updated and points at the
            expected media.

        :CaseLevel: Integration
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

    @tier2
    @upgrade
    def test_positive_update_medias(self):
        """Create an operating system that points at media entity and
        then update it to point to another multiple different medias.

        :id: 756c4aa8-278d-488e-b48f-a8d2ace4526e

        :expectedresults: The operating system is updated and points at the
            expected medias.

        :CaseLevel: Integration
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

    @tier2
    @upgrade
    def test_positive_update_template(self):
        """Create an operating system that points at config template and
        then update it to point to another template

        :id: 02125a7a-905a-492a-a49b-768adf4ac00c

        :expectedresults: The operating system is updated and points at the
            expected config template.

        :CaseLevel: Integration
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
    def test_negative_update_name(self):
        """Create operating system entity providing the initial name,
        then update its name to invalid one.

        :id: 3ba55d6e-99cb-4878-b41b-a59476d1db58

        :expectedresults: Operating system entity is not updated

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    os = entities.OperatingSystem(
                        id=os.id, name=new_name).update(['name'])

    @tier1
    def test_negative_update_major_version(self):
        """Create operating entity providing the initial major version,
        then update that version to invalid one.

        :id: de07c2f7-0896-493d-976c-e9f3a8a57025

        :expectedresults: Operating system entity is not updated

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem().create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(id=os.id, major='-20').update(['major'])

    @tier1
    def test_negative_update_minor_version(self):
        """Create operating entity providing the initial minor version,
        then update that version to invalid one.

        :id: 130d028f-302d-4c20-b35c-c7f024f3897b

        :expectedresults: Operating system entity is not updated

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem(minor=gen_string('numeric')).create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(
                id=os.id, minor='INVALID_VERSION').update(['minor'])

    @tier1
    def test_negative_update_os_family(self):
        """Create operating entity providing the initial os family, then
        update that family to invalid one.

        :id: fc11506e-8a46-470b-bde0-6fc5db98463f

        :expectedresults: Operating system entity is not updated

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem(family=OPERATING_SYSTEMS[0]).create()
        with self.assertRaises(HTTPError):
            entities.OperatingSystem(
                id=os.id, family='NON_EXISTENT_OS').update(['family'])

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create new operating system entity and then delete it.

        :id: 3dbffb56-ad99-441d-921c-0fad6504d257

        :expectedresults: Operating System entity is deleted successfully

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                os = entities.OperatingSystem(name=name).create()
                os.delete()
                with self.assertRaises(HTTPError):
                    os.read()
