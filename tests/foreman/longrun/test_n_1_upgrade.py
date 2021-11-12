"""Test class for N-1 upgrade feature

:Requirement: Satellite one version ahead from Capsule

:CaseAutomation: ManualOnly

:CaseLevel: System

:CaseComponent: Capsule

:Assignee: lpramuk

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest


@pytest.mark.stubbed
@pytest.mark.tier3
def test_n_1_setup():
    """
    Prepare the environment to test the N-1 Capsule sync scenarios.

    :id: 62c86858-4803-417a-80c7-0070df228355

    :steps:
        1. Login Satellite with admin rights.
        2. Add the Red Hat and Custom Repository.
        3. Create the lifecycle environment.
        4. Create the Content view and select all the repository.
        5. Publish the content view and promote the content view with created lifecycle
            environment.
        6. Create the activation key and add the content view.
        7. Add the subscription, if it is missing in the activation key.

    :expectedresults: Initial setup should complete successfully
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_capsule_optimize_sync():
    """
    Check the N-1 Capsule sync operation when the synchronization type is Optimize.

    :id: 482da3ab-a29f-46cd-91cc-d3bd7937bd11

    :steps:
        1. Go to the infrastructure --> Capsules
        2. Add the content view in the capsules
        3. Click on the synchronization and select the optimize sync.
        4. Optimize sync starts successfully

    :expectedresults:
        1. Optimize sync should be start and complete successfully.
        2. All the contents properly populate on the capsule side.
        3. Event of the optimize sync populated in the Monitors--> task section.
        4. Check the events in the log section.
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_capsule_complete_sync():
    """
    Check the N-1 Capsule sync operation when the synchronization type is Complete.

    :id: b8f7ecbf-e359-495e-acd9-3e0ba44d8c12

    :steps:
        1. Go to the infrastructure --> Capsules
        2. Add the content view in the capsules
        3. Click on the synchronization and select the complete sync.
        4. Complete Sync starts successfully

    :expectedresults:
        1. Optimize sync should be start and complete successfully.
        2. All the contents properly populate on the capsule side.
        3. Event of the optimize sync populated in the Monitors--> task section.
        4. Check the events in log section.
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_content_update_on_capsule_registered_host():
    """
    Check the packages update on the capsule registered content host.

    :id: d331c36f-f69b-4504-89d7-f87c808b1c16

    :steps:
        1. Go to the hosts --> Content-hosts
        2. Add the content view in the capsules
        3. Click on "Register Content host"
        4. Select the N-1 capsule and copy the command mentioned like
              a. curl --insecure --output katello-ca-consumer-latest.noarch.rpm
                 https://capsule.com/pub/katello-ca-consumer-latest.noarch.rpm
              b. yum localinstall katello-ca-consumer-latest.noarch.rpm
        5. Download the katello-ca-consumer certificate and install it on the content host.
        6. Check the Custom repository's contents.
        7. Check the Red Hat repositories contents.
        8. Install the katello-agent from the custom repo.
        9. Install few packages from Red Hat repository.

    :expectedresults:
        1. Content host should be registered successfully from N-1 Capsule.
        2. All the contents should be properly reflected on the registered host side..
        3. Katello-agent package should be successfully installed via custom repo.
        4. Few Red Hat Packages should be successfully installed via Red Hat repo.
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_provisioning_from_n_1_capsule():
    """
    Check the RHEL7/8 provisioning from N-1 Capsule.

    :id: c65e4812-c461-41b7-975a-6ac34f398232

    :steps:
        1. Create the activation key of all the required RHEL8 contents.
        2. Create the DNS name, subnet, and hostgroup.
        3. Provision the RHEL8 host from the N-1 Capsule.

    :expectedresults:
        1. Host provisioned successfully.
        2. katello-agent and puppet agent packages should be installed after provisioning
        3. Provisioned host should be registered.
        4. Remote job should be executed on that provisioned host successfully.
        5. Host counts should be updated for the puppet environment.
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_puppet_environment_import():
    """
    Check the puppet environment import from satellite and N-1 capsule

    :id: 59facd73-60be-4eb0-b389-4d2ae6886c35

    :steps:
        1. import the puppet environment from satellite.
        2. import the puppet environment from N-1 capsule.

    :expectedresults:
        1. Puppet environment should be imported successfully from satellite
        as well as capsule.
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_puppet_fact_update():
    """
    Verify the facts successfully fetched from the N-1 Capsule's provisioned host

    :id: dc15da39-c75d-4f1b-8590-3df36c6531de

    :steps:
        1. Register host with N-1 Capsule content source.
        2. Add the activation key with tool report.
        3. Install the puppte agent on the content host.
        4. Update some puppet facts in the smart class

    :expectedresults:
        1. Changed facts should be reflected on the content host
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_ansible_role_import():
    """
    Check the Ansible import operation from N-1 capsule

    :id: 8be51495-2398-45eb-a192-24a4ea09a1d7

    :steps:
        1. Import ansible roles from N-1 capsule.

    :expectedresults:
        1. Roles import should work from N-1 Capsule.
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def rex_job_execution_from_n_1_capsule():
    """
    Check the updated ansible templates should work as expected from content-host
    (part of n-1 capsule).

    :id: d5f4ab23-109f-43f4-934a-cc8f948211f1

    :steps:
        1. Update the ansible template.
        2. Run the ansible roles on N-1 registered content host

    :expectedresults:
        1. Ansible job should be completed successfully.
    """
