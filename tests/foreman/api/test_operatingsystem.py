"""Unit tests for the ``operatingsystems`` paths.

References for the relevant paths can be found on your Satellite:

* http://<sat6>/apidoc/v2/operatingsystems.html
* http://<sat6>/apidoc/v2/parameters.html


:Requirement: Operatingsystem

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
from http.client import NOT_FOUND

import pytest
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.constants import OPERATING_SYSTEMS
from robottelo.utils.datafactory import invalid_values_list
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_data_list
from robottelo.utils.issue_handlers import is_open


class TestOperatingSystemParameter:
    """Tests for operating system parameters."""

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_verify_bugzilla_1114640(self, target_sat):
        """Create a parameter for operating system 1.

        :id: e817ae43-226c-44e3-b559-62b8d394047b

        :expectedresults: A parameter is created and can be read afterwards.

        :CaseImportance: Critical
        """
        # Check whether OS 1 exists.
        os1 = target_sat.api.OperatingSystem(id=1).read_raw()
        if os1.status_code == NOT_FOUND and target_sat.api.OperatingSystem().create().id != 1:
            pytest.skip('Cannot execute test, as operating system 1 is not available.')

        # Create and read a parameter for operating system 1. The purpose of
        # this test is to make sure an HTTP 422 is not returned, but we're also
        # going to verify the name and value of the parameter, just for good
        # measure.
        name = gen_string('utf8')
        value = gen_string('utf8')
        os_param = target_sat.api.OperatingSystemParameter(
            name=name, operatingsystem=1, value=value
        ).create()
        assert os_param.name == name
        assert os_param.value == value


class TestOperatingSystem:
    """Tests for operating systems."""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_with_name(self, name, target_sat):
        """Create operating system with valid name only

        :id: e95707bf-3344-4d85-866f-4642a8f66cff

        :parametrized: yes

        :expectedresults: Operating system entity is created and has proper
            name

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(name=name).create()
        assert os.name == name

    @pytest.mark.tier1
    @pytest.mark.parametrize('os_family', **parametrized(OPERATING_SYSTEMS))
    def test_positive_create_with_os_family(self, os_family, target_sat):
        """Create operating system with every OS family possible

        :id: 6ad32d22-53cc-4bab-ac10-f466f75d7cc6

        :parametrized: yes

        :expectedresults: Operating system entity is created and has proper OS
            family assigned

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        if is_open('BZ:1709683') and os_family == 'Debian':
            pytest.skip("BZ 1709683")
        os = target_sat.api.OperatingSystem(family=os_family).create()
        assert os.family == os_family

    @pytest.mark.tier1
    def test_positive_create_with_minor_version(self, target_sat):
        """Create operating system with minor version

        :id: fc2e36ca-eb5c-440b-957e-390cd9820945

        :expectedresults: Operating system entity is created and has proper
            minor version

        :CaseImportance: Critical
        """
        minor_version = gen_string('numeric')
        os = target_sat.api.OperatingSystem(minor=minor_version).create()
        assert os.minor == minor_version

    @pytest.mark.tier1
    def test_positive_read_minor_version_as_string(self, target_sat):
        """Create an operating system with an integer minor version.

        :id: b45e0b94-62f7-45ff-a19e-83c7a0f51339

        :expectedresults: The minor version can be read back as a string.

        :CaseImportance: Critical

        :BZ: 1230902
        """
        minor = int(gen_string('numeric', random.randint(1, 16)))
        operating_sys = target_sat.api.OperatingSystem(minor=minor).create()
        assert operating_sys.minor == str(minor)

    @pytest.mark.tier1
    @pytest.mark.parametrize('desc', **parametrized(valid_data_list()))
    def test_positive_create_with_description(self, desc, target_sat):
        """Create operating system with description

        :id: 980e6411-da11-4fec-ae46-47722367ae40

        :parametrized: yes

        :expectedresults: Operating system entity is created and has proper
            description

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        os = target_sat.api.OperatingSystem(name=name, description=desc).create()
        assert os.name == name
        assert os.description == desc

    @pytest.mark.tier1
    @pytest.mark.parametrize('pass_hash', **parametrized(('SHA256', 'SHA512')))
    def test_positive_create_with_password_hash(self, pass_hash, target_sat):
        """Create operating system with valid password hash option

        :id: 00830e71-b414-41ab-bc8f-03fd2fbd5a84

        :parametrized: yes

        :expectedresults: Operating system entity is created and has proper
            password hash type

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(password_hash=pass_hash).create()
        assert os.password_hash == pass_hash

    @pytest.mark.tier2
    def test_positive_create_with_arch(self, target_sat):
        """Create an operating system that points at an architecture.

        :id: 6a3f7183-b0bf-4834-8c69-a49fe8d7ee5a

        :expectedresults: The operating system is created and points at the
            given architecture.

        :CaseLevel: Integration
        """
        arch = target_sat.api.Architecture().create()
        operating_sys = target_sat.api.OperatingSystem(architecture=[arch]).create()
        assert len(operating_sys.architecture) == 1
        assert operating_sys.architecture[0].id == arch.id

    @pytest.mark.tier2
    def test_positive_create_with_archs(self, target_sat):
        """Create an operating system that points at multiple different
        architectures.

        :id: afd26c6a-bf54-4883-baa5-95f263e6fb36

        :expectedresults: The operating system is created and points at the
            expected architectures.

        :CaseLevel: Integration
        """
        amount = range(random.randint(3, 5))
        archs = [target_sat.api.Architecture().create() for _ in amount]
        operating_sys = target_sat.api.OperatingSystem(architecture=archs).create()
        assert len(operating_sys.architecture) == len(amount)
        assert {arch.id for arch in operating_sys.architecture} == {arch.id for arch in archs}

    @pytest.mark.tier2
    def test_positive_create_with_ptable(self, target_sat):
        """Create an operating system that points at a partition table.

        :id: bef37ff9-d8fa-4518-9073-0518aa9f9a42

        :expectedresults: The operating system is created and points at the
            given partition table.

        :CaseLevel: Integration
        """
        ptable = target_sat.api.PartitionTable().create()
        operating_sys = target_sat.api.OperatingSystem(ptable=[ptable]).create()
        assert len(operating_sys.ptable) == 1
        assert operating_sys.ptable[0].id == ptable.id

    @pytest.mark.tier2
    def test_positive_create_with_ptables(self, target_sat):
        """Create an operating system that points at multiple different
        partition tables.

        :id: ed48a279-a222-45ce-81e4-72ae9422482a

        :expectedresults: The operating system is created and points at the
            expected partition tables.

        :CaseLevel: Integration
        """
        amount = range(random.randint(3, 5))
        ptables = [target_sat.api.PartitionTable().create() for _ in amount]
        operating_sys = target_sat.api.OperatingSystem(ptable=ptables).create()
        assert len(operating_sys.ptable) == len(amount)
        assert {ptable.id for ptable in operating_sys.ptable} == {ptable.id for ptable in ptables}

    @pytest.mark.tier2
    def test_positive_create_with_media(self, module_org, module_target_sat):
        """Create an operating system that points at a media.

        :id: 56fadee4-c676-48b6-a2db-e6fef9d2a575

        :expectedresults: The operating system is created and points at the
            given media.

        :CaseLevel: Integration
        """
        medium = module_target_sat.api.Media(organization=[module_org]).create()
        operating_sys = module_target_sat.api.OperatingSystem(medium=[medium]).create()
        assert len(operating_sys.medium) == 1
        assert operating_sys.medium[0].id == medium.id

    @pytest.mark.tier2
    def test_positive_create_with_template(self, module_org, module_target_sat):
        """Create an operating system that points at a provisioning template.

        :id: df73ecba-5a1c-4201-9c2f-b2e03e8fec25

        :expectedresults: The operating system is created and points at the
            expected provisioning template.

        :CaseLevel: Integration
        """
        template = module_target_sat.api.ProvisioningTemplate(organization=[module_org]).create()
        operating_sys = module_target_sat.api.OperatingSystem(
            provisioning_template=[template]
        ).create()
        assert len(operating_sys.provisioning_template) == 1
        assert operating_sys.provisioning_template[0].id == template.id

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_invalid_name(self, name, target_sat):
        """Try to create operating system entity providing an invalid
        name

        :id: cd4286fd-7128-4385-9c8d-ef979c22ee38

        :parametrized: yes

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(name=name).create()

    @pytest.mark.tier1
    def test_negative_create_with_invalid_os_family(self, target_sat):
        """Try to create operating system entity providing an invalid
        operating system family

        :id: 205a433d-750b-4b06-9fd4-274303780d6d

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(family='NON_EXISTENT_OS').create()

    @pytest.mark.tier1
    def test_negative_create_with_too_long_description(self, target_sat):
        """Try to create operating system entity providing too long
        description value

        :id: fe5fc36a-5994-4d8a-91f6-0425765b8c39

        :expectedresults: Operating system entity is not created

        :BZ: 1328935

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(description=gen_string('alphanumeric', 256)).create()

    @pytest.mark.skip_if_open('BZ:2101435')
    @pytest.mark.tier1
    @pytest.mark.parametrize('major_version', **parametrized((gen_string('numeric', 6), '', '-6')))
    def test_negative_create_with_invalid_major_version(self, major_version, target_sat):
        """Try to create operating system entity providing incorrect
        major version value (More than 5 characters, empty value, negative
        number)

        :id: f2646bc2-d639-4079-bdcb-ff76679f1457

        :parametrized: yes

        :expectedresults: Operating system entity is not created

        :BZ: 2101435

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(major=major_version).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('minor_version', **parametrized((gen_string('numeric', 17), '-5')))
    def test_negative_create_with_invalid_minor_version(self, minor_version, target_sat):
        """Try to create operating system entity providing incorrect
        minor version value (More than 16 characters and negative number)

        :id: dec4b456-153c-4a66-8b8e-b12ac7800e51

        :parametrized: yes

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(minor=minor_version).create()

    @pytest.mark.tier1
    def test_negative_create_with_invalid_password_hash(self, target_sat):
        """Try to create operating system entity providing invalid
        password hash value

        :id: 9cfcb6d4-0601-4fc7-bd1e-8b8327129a69

        :expectedresults: Operating system entity is not created

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(password_hash='INVALID_HASH').create()

    @pytest.mark.tier1
    def test_negative_create_with_same_name_and_version(self, target_sat):
        """Create operating system providing valid name and major
        version. Then try to create operating system using the same name and
        version

        :id: 3f2ca323-7789-4d2b-bf21-2454317147ff

        :expectedresults: Second operating system entity is not created

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem().create()
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(name=os.name, major=os.major).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
    def test_positive_update_name(self, new_name, target_sat):
        """Create operating system entity providing the initial name,
        then update its name to another valid name.

        :id: 2898e16a-865a-4de6-b2a5-bb0934fc2b76

        :parametrized: yes

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem().create()
        os = target_sat.api.OperatingSystem(id=os.id, name=new_name).update(['name'])
        assert os.name == new_name

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_desc', **parametrized(valid_data_list()))
    def test_positive_update_description(self, new_desc, target_sat):
        """Create operating entity providing the initial description,
        then update that description to another valid one.

        :id: c809700a-b6ab-4651-9bd0-d0d9bd6a47dd

        :parametrized: yes

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(description=gen_string('utf8')).create()
        os = target_sat.api.OperatingSystem(id=os.id, description=new_desc).update(['description'])
        assert os.description == new_desc

    @pytest.mark.tier1
    def test_positive_update_major_version(self, target_sat):
        """Create operating entity providing the initial major version,
        then update that version to another valid one.

        :id: e57fd4a3-f0ae-49fb-bd84-9a6ec606a2a2

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem().create()
        new_major_version = gen_string('numeric', 5)
        os = target_sat.api.OperatingSystem(id=os.id, major=new_major_version).update(['major'])
        assert os.major == new_major_version

    @pytest.mark.tier1
    def test_positive_update_minor_version(self, target_sat):
        """Create operating entity providing the initial minor version,
        then update that version to another valid one.

        :id: ca36f7cf-4487-4743-be06-52c5f47ffe71

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(minor=gen_string('numeric')).create()
        new_minor_version = gen_string('numeric')
        os = target_sat.api.OperatingSystem(id=os.id, minor=new_minor_version).update(['minor'])
        assert os.minor == new_minor_version

    @pytest.mark.tier1
    def test_positive_update_os_family(self, target_sat):
        """Create operating entity providing the initial os family, then
        update that family to another valid one from the list.

        :id: 3d1f8fdc-d2de-4277-a0ba-07228a2fae82

        :expectedresults: Operating system entity is created and updated
            properly

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(family=OPERATING_SYSTEMS[0]).create()
        new_os_family = OPERATING_SYSTEMS[random.randint(1, len(OPERATING_SYSTEMS) - 1)]
        os = target_sat.api.OperatingSystem(id=os.id, family=new_os_family).update(['family'])
        assert os.family == new_os_family

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_arch(self, target_sat):
        """Create an operating system that points at an architecture and
        then update it to point to another architecture

        :id: ad69b4a3-6371-4516-b5ce-f6298edf35b3

        :expectedresults: The operating system is updated and points at the
            expected architecture.

        :CaseLevel: Integration
        """
        arch_1 = target_sat.api.Architecture().create()
        arch_2 = target_sat.api.Architecture().create()
        os = target_sat.api.OperatingSystem(architecture=[arch_1]).create()
        assert len(os.architecture) == 1
        assert os.architecture[0].id == arch_1.id
        os = target_sat.api.OperatingSystem(id=os.id, architecture=[arch_2]).update(
            ['architecture']
        )
        assert len(os.architecture) == 1
        assert os.architecture[0].id == arch_2.id

    @pytest.mark.tier2
    def test_positive_update_ptable(self, target_sat):
        """Create an operating system that points at partition table and
        then update it to point to another partition table

        :id: 0dde5372-4b90-4c83-b497-31e94065adab

        :expectedresults: The operating system is updated and points at the
            expected partition table.

        :CaseLevel: Integration
        """
        ptable_1 = target_sat.api.PartitionTable().create()
        ptable_2 = target_sat.api.PartitionTable().create()
        os = target_sat.api.OperatingSystem(ptable=[ptable_1]).create()
        assert len(os.ptable) == 1
        assert os.ptable[0].id == ptable_1.id
        os = target_sat.api.OperatingSystem(id=os.id, ptable=[ptable_2]).update(['ptable'])
        assert len(os.ptable) == 1
        assert os.ptable[0].id == ptable_2.id

    @pytest.mark.tier2
    def test_positive_update_media(self, module_org, module_target_sat):
        """Create an operating system that points at media entity and
        then update it to point to another media

        :id: 18b5f6b5-52ab-4722-8412-f0de85ad20fe

        :expectedresults: The operating system is updated and points at the
            expected media.

        :CaseLevel: Integration
        """
        media_1 = module_target_sat.api.Media(organization=[module_org]).create()
        media_2 = module_target_sat.api.Media(organization=[module_org]).create()
        os = module_target_sat.api.OperatingSystem(medium=[media_1]).create()
        assert len(os.medium) == 1
        assert os.medium[0].id == media_1.id
        os = module_target_sat.api.OperatingSystem(id=os.id, medium=[media_2]).update(['medium'])
        assert len(os.medium) == 1
        assert os.medium[0].id == media_2.id

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_medias(self, module_org, module_target_sat):
        """Create an operating system that points at media entity and
        then update it to point to another multiple different medias.

        :id: 756c4aa8-278d-488e-b48f-a8d2ace4526e

        :expectedresults: The operating system is updated and points at the
            expected medias.

        :CaseLevel: Integration
        """
        initial_media = module_target_sat.api.Media(organization=[module_org]).create()
        os = module_target_sat.api.OperatingSystem(medium=[initial_media]).create()
        assert len(os.medium) == 1
        assert os.medium[0].id == initial_media.id
        amount = range(random.randint(3, 5))
        medias = [module_target_sat.api.Media().create() for _ in amount]
        os = module_target_sat.api.OperatingSystem(id=os.id, medium=medias).update(['medium'])
        assert len(os.medium) == len(amount)
        assert {medium.id for medium in os.medium} == {medium.id for medium in medias}

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_template(self, module_org, module_target_sat):
        """Create an operating system that points at provisioning template and
        then update it to point to another template

        :id: 02125a7a-905a-492a-a49b-768adf4ac00c

        :expectedresults: The operating system is updated and points at the
            expected provisioning template.

        :CaseLevel: Integration
        """
        template_1 = module_target_sat.api.ProvisioningTemplate(organization=[module_org]).create()
        template_2 = module_target_sat.api.ProvisioningTemplate(organization=[module_org]).create()
        os = module_target_sat.api.OperatingSystem(provisioning_template=[template_1]).create()
        assert len(os.provisioning_template) == 1
        assert os.provisioning_template[0].id == template_1.id
        os = module_target_sat.api.OperatingSystem(
            id=os.id, provisioning_template=[template_2]
        ).update(['provisioning_template'])
        assert len(os.provisioning_template) == 1
        assert os.provisioning_template[0].id == template_2.id

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, new_name, target_sat):
        """Create operating system entity providing the initial name,
        then update its name to invalid one.

        :id: 3ba55d6e-99cb-4878-b41b-a59476d1db58

        :parametrized: yes

        :expectedresults: Operating system entity is not updated

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem().create()
        with pytest.raises(HTTPError):
            os = target_sat.api.OperatingSystem(id=os.id, name=new_name).update(['name'])

    @pytest.mark.skip_if_open('BZ:2101435')
    @pytest.mark.tier1
    def test_negative_update_major_version(self, target_sat):
        """Create operating entity providing the initial major version,
        then update that version to invalid one.

        :id: de07c2f7-0896-493d-976c-e9f3a8a57025

        :expectedresults: Operating system entity is not updated

        :BZ: 2101435

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem().create()
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(id=os.id, major='-20').update(['major'])

    @pytest.mark.tier1
    def test_negative_update_minor_version(self, target_sat):
        """Create operating entity providing the initial minor version,
        then update that version to invalid one.

        :id: 130d028f-302d-4c20-b35c-c7f024f3897b

        :expectedresults: Operating system entity is not updated

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(minor=gen_string('numeric')).create()
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(id=os.id, minor='INVALID_VERSION').update(['minor'])

    @pytest.mark.tier1
    def test_negative_update_os_family(self, target_sat):
        """Create operating entity providing the initial os family, then
        update that family to invalid one.

        :id: fc11506e-8a46-470b-bde0-6fc5db98463f

        :expectedresults: Operating system entity is not updated

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(family=OPERATING_SYSTEMS[0]).create()
        with pytest.raises(HTTPError):
            target_sat.api.OperatingSystem(id=os.id, family='NON_EXISTENT_OS').update(['family'])

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_delete(self, name, target_sat):
        """Create new operating system entity and then delete it.

        :id: 3dbffb56-ad99-441d-921c-0fad6504d257

        :parametrized: yes

        :expectedresults: Operating System entity is deleted successfully

        :CaseImportance: Critical
        """
        os = target_sat.api.OperatingSystem(name=name).create()
        os.delete()
        with pytest.raises(HTTPError):
            os.read()
