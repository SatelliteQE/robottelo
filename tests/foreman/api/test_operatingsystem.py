"""Provisioning tests

:Requirement: Provisioning

:CaseAutomation: Automated

:CaseComponent: Provisioning

:Team: Rocket

:CaseImportance: Critical

"""

from http.client import NOT_FOUND
import random

from fauxfactory import gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.constants import OPERATING_SYSTEMS
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
)


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

    @pytest.mark.e2e
    @pytest.mark.upgrade
    def test_positive_end_to_end_os(self, module_target_sat, module_org, module_architecture):
        """End-to-end test for Operating system

        :id: ecf2196d-96dd-4ed2-abfa-a5ffade75d91

        :steps:
            1. Create OS
            2. Check OS is created with all given fields
            3. Read OS
            4. Update OS
            5. Check OS is updated with all given fields
            6. Delete OS
            7. Check if OS is deleted

        :expectedresults: All CRUD operations are performed successfully.

        :BZ: 2101435, 1230902
        """
        name = gen_string('alpha')
        desc = gen_string('alpha')
        os_family = 'Redhat'
        minor_version = gen_string('numeric')
        major_version = gen_string('numeric', 5)
        pass_hash = 'SHA256'
        ptable = module_target_sat.api.PartitionTable().create()
        medium = module_target_sat.api.Media(organization=[module_org]).create()
        template = module_target_sat.api.ProvisioningTemplate(
            organization=[module_org],
        ).create()
        # Create OS
        os = module_target_sat.api.OperatingSystem(
            name=name,
            description=desc,
            minor=minor_version,
            major=major_version,
            family=os_family,
            architecture=[module_architecture],
            password_hash=pass_hash,
            provisioning_template=[template],
            ptable=[ptable],
            medium=[medium],
        ).create()
        assert os.name == name
        assert os.family == os_family
        assert os.minor == str(minor_version)
        assert os.major == major_version
        assert os.description == desc
        assert os.architecture[0].id == module_architecture.id
        assert os.password_hash == pass_hash
        assert os.ptable[0].id == ptable.id
        assert os.provisioning_template[0].id == template.id
        assert os.medium[0].id == medium.id
        # Read OS
        os = module_target_sat.api.OperatingSystem(id=os.id).read()
        assert os.name == name
        assert os.family == os_family
        assert os.minor == minor_version
        assert os.major == major_version
        assert os.description == desc
        assert os.architecture[0].id == module_architecture.id
        assert os.password_hash == pass_hash
        assert str(ptable.id) in str(os.ptable)
        assert str(template.id) in str(os.provisioning_template)
        assert os.medium[0].id == medium.id
        new_name = gen_string('alpha')
        new_desc = gen_string('alpha')
        new_os_family = 'Rhcos'
        new_minor_version = gen_string('numeric')
        new_major_version = gen_string('numeric', 5)
        new_pass_hash = 'SHA512'
        new_arch = module_target_sat.api.Architecture().create()
        new_ptable = module_target_sat.api.PartitionTable().create()
        new_medium = module_target_sat.api.Media(organization=[module_org]).create()
        new_template = module_target_sat.api.ProvisioningTemplate(
            organization=[module_org]
        ).create()
        # Update OS
        os = module_target_sat.api.OperatingSystem(
            id=os.id,
            name=new_name,
            description=new_desc,
            minor=new_minor_version,
            major=new_major_version,
            family=new_os_family,
            architecture=[new_arch],
            password_hash=new_pass_hash,
            provisioning_template=[new_template],
            ptable=[new_ptable],
            medium=[new_medium],
        ).update(
            [
                'name',
                'description',
                'minor',
                'major',
                'family',
                'architecture',
                'password_hash',
                'provisioning_template',
                'ptable',
                'medium',
            ]
        )
        assert os.name == new_name
        assert os.family == new_os_family
        assert os.minor == new_minor_version
        assert os.major == new_major_version
        assert os.description == new_desc
        assert os.architecture[0].id == new_arch.id
        assert os.password_hash == new_pass_hash
        assert os.ptable[0].id == new_ptable.id
        assert os.provisioning_template[0].id == new_template.id
        assert os.medium[0].id == new_medium.id
        # Delete OS
        module_target_sat.api.OperatingSystem(id=os.id).delete()
        with pytest.raises(HTTPError):
            module_target_sat.api.OperatingSystem(id=os.id).read()

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

    @pytest.mark.tier2
    def test_positive_create_with_archs(self, target_sat):
        """Create an operating system that points at multiple different
        architectures.

        :id: afd26c6a-bf54-4883-baa5-95f263e6fb36

        :expectedresults: The operating system is created and points at the
            expected architectures.

        """
        amount = range(random.randint(3, 5))
        archs = [target_sat.api.Architecture().create() for _ in amount]
        operating_sys = target_sat.api.OperatingSystem(architecture=archs).create()
        assert len(operating_sys.architecture) == len(amount)
        assert {arch.id for arch in operating_sys.architecture} == {arch.id for arch in archs}

    @pytest.mark.tier2
    def test_positive_create_with_ptables(self, target_sat):
        """Create an operating system that points at multiple different
        partition tables.

        :id: ed48a279-a222-45ce-81e4-72ae9422482a

        :expectedresults: The operating system is created and points at the
            expected partition tables.

        """
        amount = range(random.randint(3, 5))
        ptables = [target_sat.api.PartitionTable().create() for _ in amount]
        operating_sys = target_sat.api.OperatingSystem(ptable=ptables).create()
        assert len(operating_sys.ptable) == len(amount)
        assert {ptable.id for ptable in operating_sys.ptable} == {ptable.id for ptable in ptables}

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

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_medias(self, module_org, module_target_sat):
        """Create an operating system that points at media entity and
        then update it to point to another multiple different medias.

        :id: 756c4aa8-278d-488e-b48f-a8d2ace4526e

        :expectedresults: The operating system is updated and points at the
            expected medias.

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
