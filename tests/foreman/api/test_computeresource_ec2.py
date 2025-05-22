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


@pytest.mark.run_in_one_thread
class TestEC2CustomImageFinishTemplateProvisioning:
    """EC2 Host Provisioning Tests with Custom Image"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(
        self,
        request,
        sat_ec2_domain,
        module_ec2_cr,
    ):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.ec2.region
        request.cls.hostname = f'test{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{sat_ec2_domain.name}'.lower()

    @pytest.fixture(scope='class')
    def class_host_custom_ft(
        self,
        sat_ec2,
        module_ec2_finishimg,
        sat_ec2_default_architecture,
        sat_ec2_domain,
        sat_ec2_loc,
        sat_ec2_org,
        sat_ec2_default_os,
        ec2_hostgroup,
    ):
        """
        Provisions the host on EC2 using Finish template
        Later in tests this host will be used to perform assertions
        """
        with sat_ec2.skip_yum_update_during_provisioning(template='Kickstart default finish'):
            host = sat_ec2.api.Host(
                architecture=sat_ec2_default_architecture,
                domain=sat_ec2_domain,
                hostgroup=ec2_hostgroup,
                organization=sat_ec2_org,
                operatingsystem=sat_ec2_default_os,
                location=sat_ec2_loc,
                name=self.hostname,
                provision_method='image',
                image=module_ec2_finishimg,
                root_pass=gen_string('alphanumeric'),
            ).create()
            yield host

    @pytest.fixture(scope='class')
    def ec2client_host(self, ec2client, class_host_custom_ft):
        """Returns the EC2 Client Host object to perform the assertions"""

        return ec2client.get_vm(name=class_host_custom_ft.name.split('.')[0])

    @pytest.mark.upgrade
    @pytest.mark.parametrize('sat_ec2', ['sat'], indirect=True)
    @pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
    def test_positive_ec2_custom_image_host_provisioned(
        self, class_host_custom_ft, ec2client_host, setting_update
    ):
        """Host can be provisioned on EC2 using Custom Image

        :id: ba056978-f563-4836-8336-e1d1de97ff08

        :CaseImportance: Critical

        :steps:
            1. Create an EC2 Compute Resource with Custom Image and provision host.

        :expectedresults:
            1. The host should be provisioned on EC2 using Custom Image
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
            5. The host Name and Platform should be same on ec2 Cloud as provided during
               provisioned

        """
        assert class_host_custom_ft.name == self.fullhostname
        assert class_host_custom_ft.build_status_label == "Installed"
        assert class_host_custom_ft.ip == ec2client_host.ip

        # ec2 cloud
        assert self.hostname.lower() == ec2client_host.name
