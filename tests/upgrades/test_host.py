"""Test Host/Provisioning related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string


class TestScenarioPositiveGCEHostComputeResource:
    """The host can be provisioned on GCE CR created in previous version

    :steps:

        1. Create a GCE Compute Resource in Pre-upgrade Satellite.
        2. Provision hosts on the GCE Compute Resource.
        3. Upgrade the Satellite to the next or latest version.
        4. After the upgrade, you can modify the attributes of Compute Resource.
        5. Provision the new host on the GCE Compute Resource upgraded Satellite.

    :expectedresults:

        1. The host should be provisioned on GCE CR created in previous version
        2. The GCE CR attributes should be manipulated
    """

    @pytest.fixture
    def class_setup(self, request, gce_latest_rhel_uuid, sat_gce_domain):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.mtype = 'g1-small'
        request.cls.network = 'default'
        request.cls.volsize = '20'
        request.cls.hostname = f'test{gen_string("alpha")}'

        request.cls.fullhostname = f'{self.hostname}.{sat_gce_domain.name}'.lower()

        request.cls.compute_attrs = {
            'image_id': gce_latest_rhel_uuid,
            'machine_type': self.mtype,
            'network': self.network,
            'associate_external_ip': True,
            'volumes_attributes': {'0': {'size_gb': self.volsize}},
        }

    @pytest.fixture
    def class_host(
        self,
        sat_gce,
        googleclient,
        sat_gce_default_architecture,
        sat_gce_domain,
        gce_hostgroup,
        sat_gce_org,
        sat_gce_default_os,
        sat_gce_loc,
        gce_latest_rhel_uuid,
        module_gce_finishimg,
        module_gce_compute,
        class_setup,
    ):
        """Provisions the host on GCE

        Later in tests this host will be used to perform assertions
        """
        host = sat_gce.api.Host(
            architecture=sat_gce_default_architecture,
            compute_attributes=self.compute_attrs,
            domain=sat_gce_domain,
            hostgroup=gce_hostgroup,
            organization=sat_gce_org,
            operatingsystem=sat_gce_default_os,
            location=sat_gce_loc,
            name=self.hostname,
            provision_method='image',
            image=module_gce_finishimg,
            root_pass=gen_string('alphanumeric'),
        ).create()
        yield host

    def google_host(self, googleclient):
        """Returns the Google Client Host object to perform the assertions"""
        return googleclient.get_vm(name='{}'.format(self.fullhostname.replace('.', '-')))

    @pytest.mark.pre_upgrade
    @pytest.mark.tier1
    def test_pre_create_gce_cr_and_host(
        self,
        class_host,
        sat_gce_org,
        sat_gce_loc,
        module_gce_compute,
        sat_gce_domain,
        gce_hostgroup,
        module_gce_finishimg,
        googleclient,
        save_test_data,
    ):
        """Host can be provisioned on Google Cloud

        :id: 889975f2-56ca-4584-95a7-21c513969630

        :CaseLevel: Component

        ::CaseImportance: Critical

        :steps:
            1. Create a GCE Compute Resource
            2. Create a Host-group with all the Global and Foreman entities but
                without Compute Profile, required to provision a host
            3. Provision a Host on Google Cloud using above GCE CR and Host-group

        :expectedresults:
            1. The host should be provisioned on Google Compute Engine
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
        """
        assert class_host.name == self.fullhostname
        assert class_host.build_status_label == 'Installed'
        assert class_host.ip == self.google_host(googleclient).ip

        save_test_data(
            {
                'provision_host_name': self.fullhostname,
                'provision_host_ip': class_host.ip,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_create_gce_cr_and_host)
    def test_post_create_gce_cr_and_host(
        self,
        sat_gce,
        request,
        class_setup,
        pre_upgrade_data,
        sat_gce_org,
        sat_gce_default_architecture,
        sat_gce_default_os,
        googleclient,
    ):
        """Host provisioned using pre-upgrade GCE CR

        :id: postupgrade-ef82143d-efef-49b2-9702-93d67ef6804c

        :steps:

            1. Postupgrade, The Compute Resource attributes can be manipulated
            2. The host can be provisioned on GCE CR created in previous satellite version

        :expectedresults:

            1. The host should be provisioned on GCE CR created in previous version
            2. The GCE CR attributes should be manipulated
        """
        pre_upgrade_host = sat_gce.api.Host().search(
            query={'search': f'name={pre_upgrade_data.provision_host_name}'}
        )[0]
        org = sat_gce.api.Organization(id=pre_upgrade_host.organization.id).read()
        loc = sat_gce.api.Location(id=pre_upgrade_host.location.id).read()
        domain = sat_gce.api.Domain(id=pre_upgrade_host.domain.id).read()
        image = sat_gce.api.Image(
            id=pre_upgrade_host.image.id, compute_resource=pre_upgrade_host.compute_resource.id
        ).read()
        gce_hostgroup = sat_gce.api.HostGroup(id=pre_upgrade_host.hostgroup.id).read()

        assert pre_upgrade_host.ip == pre_upgrade_data.provision_host_ip
        assert pre_upgrade_host.build_status_label == 'Installed'

        host = sat_gce.api.Host(
            architecture=sat_gce_default_architecture,
            compute_attributes=self.compute_attrs,
            domain=domain,
            hostgroup=gce_hostgroup,
            organization=org,
            operatingsystem=sat_gce_default_os,
            location=loc,
            name=self.hostname,
            provision_method='image',
            image=image,
            root_pass=gen_string('alphanumeric'),
        ).create()
        request.addfinalizer(pre_upgrade_host.delete)
        request.addfinalizer(host.delete)
        assert host.name == f"{self.hostname.lower()}.{domain.name}"
        assert host.build_status_label == 'Installed'
        assert host.ip == self.google_host(googleclient).ip
