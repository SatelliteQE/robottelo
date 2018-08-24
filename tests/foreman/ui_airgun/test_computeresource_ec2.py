from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import (
    FOREMAN_PROVIDERS,
    AWS_EC2_FLAVOR_T2_MICRO,
    COMPUTE_PROFILE_LARGE,
)
from robottelo.decorators import (
    run_only_on,
    tier2,
)
from robottelo.datafactory import valid_data_list
from robottelo.decorators import parametrize


@parametrize('name', **valid_data_list('ui'))
@run_only_on('sat')
@tier2
def test_positive_list_CR(session, name):
    """
    Associate (3-Large) compute profile to ec2 compute
    resource

    :id: 366abfde-06ee-4576-9c36-3910b5a4e174

    :setup: ec2 hostname, credentials, and flavor

    :steps:

        1. Create a compute resource of type ec2
        2. Provide a valid Access Key and Secret Key
        3. Select (3-Large) compute profile
        4. List Compute Resources associated with this compute profile
        5. Check if created ec2 CR is in the list

    :expectedresults: (3-Large) is associated with ec2 CR

    :Caseautomation: Automated
    """
    ec2_access_key = settings.ec2.access_key
    ec2_secret_key = settings.ec2.secret_key
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['ec2'],
            'provider_content.access_key': ec2_access_key,
            'provider_content.secret_key': ec2_secret_key,
        })
        assert session.computeresource.search(name)[0]['Name'] == name
        EC2_region = session.computeresource.read(
            name)['provider_content']['region']
        brackets = "(" + EC2_region + "-" + FOREMAN_PROVIDERS['ec2'] + ")"
        computeresource_name = (name, brackets)
        computeresource_name = " ".join(computeresource_name)
        computeresource_dict = session.computeprofile.list_resources(
            COMPUTE_PROFILE_LARGE)
        computeresource_list = []
        for CR in computeresource_dict:
            computeresource_list.append(CR['Compute Resource'])
        assert computeresource_name in computeresource_list


@parametrize('name', **valid_data_list('ui'))
@run_only_on('sat')
@tier2
def test_positive_edit_compute_profile_through_CR(session, name):
    """
    Associate custom (3-Large) compute profile to ec2 compute resource

    :id: c1bb31ae-d37d-4bdf-8fb7-130585a2b82d

    :setup: ec2 hostname and credentials, custom flavor.

    :steps:

        1. Create a compute resource of type ec2
        2. Provide a valid Access Key and Secret Key
        3. Select the created ec2 CR
        4. Click Compute Profile tab
        5. Edit (3-Large) with valid configurations and submit

    :expectedresults: The compute profile edit successfully

    :Caseautomation: Automated
    """
    ec2_access_key = settings.ec2.access_key
    ec2_secret_key = settings.ec2.secret_key
    availability_zone = settings.ec2.availability_zone
    subnet = settings.ec2.subnet
    managed_ip = settings.ec2.managed_ip
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['ec2'],
            'provider_content.access_key': ec2_access_key,
            'provider_content.secret_key': ec2_secret_key,
        })
        assert session.computeresource.search(name)[0]['Name'] == name
        session.computeresource.update_computeprofile(
            name, COMPUTE_PROFILE_LARGE, {
                'flavor': AWS_EC2_FLAVOR_T2_MICRO,
                'availability_zone': availability_zone,
                'subnet': subnet,
                'managed_ip': managed_ip,
            })
        assert session.computeresource.read_computeprofile(
            name, COMPUTE_PROFILE_LARGE)['subnet'] == subnet
