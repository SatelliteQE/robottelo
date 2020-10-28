# -*- encoding: utf-8 -*-
"""
:Requirement: Computeresource EC2

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-EC2

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cli.factory import make_compute_resource
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.org import Org
from robottelo.config import settings
from robottelo.constants import EC2_REGION_CA_CENTRAL_1
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class EC2ComputeResourceTestCase(CLITestCase):
    """EC2 ComputeResource CLI tests."""

    @classmethod
    @skip_if_not_set('ec2')
    def setUpClass(cls):
        super(EC2ComputeResourceTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.loc = make_location()
        Org.add_location({'id': cls.org['id'], 'location-id': cls.loc['id']})
        cls.aws_access_key = settings.ec2.access_key
        cls.aws_secret_key = settings.ec2.secret_key
        cls.aws_region = settings.ec2.region
        cls.aws_image = settings.ec2.image
        cls.aws_availability_zone = settings.ec2.availability_zone
        cls.aws_subnet = settings.ec2.subnet
        cls.aws_security_groups = settings.ec2.security_groups
        cls.aws_managed_ip = settings.ec2.managed_ip

    @tier1
    @upgrade
    def test_positive_create_ec2_with_custom_region(self):
        """Create a new ec2 compute resource with custom region

        :id: 28eb592d-ebf0-4659-900a-87112b3b2ad7

        :customerscenario: true

        :expectedresults: ec2 compute resource is created successfully.

        :BZ: 1456942

        :CaseAutomation: Automated

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        cr_name = gen_string(str_type='alpha')
        cr_description = gen_string(str_type='alpha')
        cr = make_compute_resource(
            {
                'name': cr_name,
                'description': cr_description,
                'provider': FOREMAN_PROVIDERS['ec2'],
                'user': self.aws_access_key,
                'password': self.aws_secret_key,
                'region': EC2_REGION_CA_CENTRAL_1,
                'organizations': self.org['name'],
                'locations': self.loc['name'],
            }
        )
        self.assertEquals(cr['name'], cr_name)
        self.assertEquals(cr['region'], EC2_REGION_CA_CENTRAL_1)
