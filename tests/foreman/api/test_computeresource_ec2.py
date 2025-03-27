"""Test class for EC2 Compute Resource

:Requirement: Computeresource EC2

:CaseAutomation: Automated

:CaseComponent: ComputeResources-EC2

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    ec2RM_FILE_URI,
    ec2RM_PLATFORM_DEFAULT,
    ec2RM_RHEL7_FT_CUSTOM_IMG_URN,
    ec2RM_VM_SIZE_DEFAULT,
)


@pytest.mark.run_in_one_thread
class TestEC2CustomImageFinishTemplateProvisioning:
    """EC2 Host Provisioning Tests with Custom Image"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(
        self,
        request,
        sat_ec2_domain,
        module_ec2_cr,
        module_ec2rm_custom_finishimg,
    ):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.ec2rm.ec2_region
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{sat_ec2_domain.name}'.lower()

        request.cls.compute_attrs = {
            "resource_group": settings.ec2rm.resource_group,
            "vm_size": ec2RM_VM_SIZE_DEFAULT,
            "username": module_ec2rm_custom_finishimg.username,
            "password": settings.ec2rm.password,
            "platform": ec2RM_PLATFORM_DEFAULT,
            "script_command": 'touch /var/tmp/text.txt',
            "script_uris": ec2RM_FILE_URI,
            "image_id": ec2RM_RHEL7_FT_CUSTOM_IMG_URN,
        }
        results = module_ec2_cr.available_networks()['results']
        nw_id = next((item for item in results if item['name'] == 'default'), None)['id']
        request.cls.interfaces_attributes = {
            "0": {
                "compute_attributes": {
                    "public_ip": "Dynamic",
                    "private_ip": "false",
                    "network": nw_id,
                }
            }
        }

    @pytest.fixture(scope='class')
    def class_host_custom_ft(
        self,
        sat_ec2,
        module_ec2rm_custom_finishimg,
        module_ec2rm_cr,
        sat_ec2_default_architecture,
        sat_ec2_domain,
        sat_ec2_loc,
        sat_ec2_org,
        sat_ec2_default_os,
    ):
        """
        Provisions the host on ec2RM using Finish template
        Later in tests this host will be used to perform assertions
        """

        with sat_ec2.skip_yum_update_during_provisioning(template='Kickstart default finish'):
            host = sat_ec2.api.Host(
                architecture=sat_ec2_default_architecture,
                build=True,
                compute_resource=module_ec2rm_cr,
                compute_attributes=self.compute_attrs,
                interfaces_attributes=self.interfaces_attributes,
                domain=sat_ec2_domain,
                organization=sat_ec2_org,
                operatingsystem=sat_ec2_default_os,
                location=sat_ec2_loc,
                name=self.hostname,
                provision_method='image',
                image=module_ec2rm_custom_finishimg,
                root_pass=gen_string('alphanumeric'),
            ).create()
            yield host
            with sat_ec2.api_factory.satellite_setting('destroy_vm_on_host_delete=True'):
                host.delete()

    @pytest.fixture(scope='class')
    def ec2client_host(self, ec2rmclient, class_host_custom_ft):
        """Returns the ec2RM Client Host object to perform the assertions"""

        return ec2rmclient.get_vm(name=class_host_custom_ft.name.split('.')[0])

    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.parametrize('sat_ec2', ['sat'], indirect=True)
    def test_positive_ec2rm_custom_image_host_provisioned(
        self, class_host_custom_ft, ec2client
    ):
        """Host can be provisioned on ec2RM using Custom Image

        :id:

        :CaseImportance: Critical

        :steps:
            1. Create a ec2RM Compute Resource with Custom Image and provision host.

        :expectedresults:
            1. The host should be provisioned on ec2RM using Custom Image
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
            5. The host Name and Platform should be same on ec2 Cloud as provided during
               provisioned

        :BZ: 1850934
        """

        assert class_host_custom_ft.name == self.fullhostname
        assert class_host_custom_ft.build_status_label == "Installed"
        assert class_host_custom_ft.ip == ec2client_host.ip

        # ec2 cloud
        assert self.hostname.lower() == ec2client_host.name
        assert ec2client_host.type == ec2RM_VM_SIZE_DEFAULT
