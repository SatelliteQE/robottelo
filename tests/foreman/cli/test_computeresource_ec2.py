"""
:Requirement: Computeresource EC2

:CaseComponent: ComputeResources-EC2

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import EC2_REGION_CA_CENTRAL_1, FOREMAN_PROVIDERS


@pytest.fixture(scope='module')
def aws(module_target_sat):
    aws = type('rhev', (object,), {})()
    aws.org = module_target_sat.cli_factory.make_org()
    aws.loc = module_target_sat.cli_factory.make_location()
    module_target_sat.cli.Org.add_location({'id': aws.org['id'], 'location-id': aws.loc['id']})
    aws.aws_access_key = settings.ec2.access_key
    aws.aws_secret_key = settings.ec2.secret_key
    aws.aws_region = settings.ec2.region
    aws.aws_image = settings.ec2.image
    aws.aws_availability_zone = settings.ec2.availability_zone
    aws.aws_subnet = settings.ec2.subnet
    aws.aws_security_groups = settings.ec2.security_groups
    aws.aws_managed_ip = settings.ec2.managed_ip
    return aws


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_ec2_with_custom_region(aws, module_target_sat):
    """Create a new ec2 compute resource with custom region

    :id: 28eb592d-ebf0-4659-900a-87112b3b2ad7

    :customerscenario: true

    :expectedresults: ec2 compute resource is created successfully.

    :BZ: 1456942

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    cr_name = gen_string(str_type='alpha')
    cr_description = gen_string(str_type='alpha')
    cr = module_target_sat.cli_factory.compute_resource(
        {
            'name': cr_name,
            'description': cr_description,
            'provider': FOREMAN_PROVIDERS['ec2'],
            'user': aws.aws_access_key,
            'password': aws.aws_secret_key,
            'region': EC2_REGION_CA_CENTRAL_1,
            'organizations': aws.org['name'],
            'locations': aws.loc['name'],
        }
    )
    assert cr['name'] == cr_name
    assert cr['region'] == EC2_REGION_CA_CENTRAL_1
