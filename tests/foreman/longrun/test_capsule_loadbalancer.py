"""Test class for Capsule Loadbalancer

:Requirement: Loadbalancer capsule

:CaseAutomation: ManualOnly

:CaseLevel: Integration

:CaseComponent: Capsule

:Assignee: akjha

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


@pytest.mark.stubbed
@pytest.mark.tier1
def initial_setup():
    """Initial setup

    :id: 6269a87a-e774-11ea-9cb6-4ceb42ab8dbc

    :Steps:
        1. Add the manifest into the satellite.
        2. Make sure the subscriptions for required repositories are enabled.
        3. Sync the repositories.
        4. Create lifecycle environment, content view and activation key for capsules and client.
        5. Install and register 2 capsules.
            5.1 Add the respective lifecycle environment to capsule and sync.
            5.2 Setup the puppetCA and puppet agent amongst the capsules accordingly.
        6. Create a host group with default values.
        7. Install loadbalancer(haproxy)
            7.1 Algorithms as follows:
                a) :HTTPS - Source
                b) :HTTP - RoundRobin
                c) :AMQP - RoundRobin
                d) :Puppet - RoundRobin
                e) :RHSM - RoundRobin
                f) :SCAP - RoundRobin
            7.2 Enable logging for haproxy (if disabled)

    :expectedresults: Initial setup complete
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_katello_cert_download_manually():
    """Download katello-ca-consumer-latest.noarch.rpm through LB

    :id: 9398d59e-e141-11ea-83a6-4ceb42ab8dbc

    :Steps: run `yum localinstall -y \
            http://loadbalancer.example.com/pub/katello-ca-consumer-latest.noarch.rpm`

    :expectedresults: Katello cert should be installed from any one of the capsules.

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_manually_register_client_using_ak():
    """Register the client using ak to the capsule

    :id: 7318c380-e149-11ea-9b17-4ceb42ab8dbc

    :Steps: run `subscription-manager register --org=Your_Organization \
            --activationkey=Your_Activation_Key \
            --serverurl=https://loadbalancer.example.com:8443/rhsm \
            --baseurl=https://loadbalancer.example.com/pulp/repos`

    :expectedresults: The client should be registered to one of the capsules

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_list_repolist():
    """List all the repositories

    :id: 973c8eb2-e14a-11ea-9a77-4ceb42ab8dbc

    :Steps: Run `yum repolist`

    :expectedresults: all the repositories are listed

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_register_using_bootstrap():
    """Register the client using bootstrap.py

    :id: ff041894-e14a-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Download the bootstrap.py and change the permissions of the script.
        2. Run `python bootstrap.py --login=admin \
                --server loadbalancer.example.com \
                --organization="Your_Organization" \
                --location="Your_Location" \
                --hostgroup="Your_Hostgroup" \
                --activationkey=your_activation_key \
                --puppet-ca-port 8141 \
                --force`

    :expectedresults:
        1. Registration should be Successful
        2. Puppet Agent Installed
        3. CA cert AutoSigned
        4. Facts Uploaded to Satellite
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_package_action_from_host():
    """Package installation on client

    :id: e8a3eefa-e14d-11ea-9a77-4ceb42ab8dbc

    :Steps: Run `yum install -y <package_name>`

    :expectedresults: Desired package is installed

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_loadbalancer_down():
    """Loadbalancer service/VM down

    :id: 4fc2656c-e14e-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Stop loadbalancer service
        2. Try installing a package
        3. Start loadbalancer service
        4. Try installing a package
        5. Power off loadbalancer VM
        6. Try installing a package
        7. Power on loadbalancer VM
        8. Try installing a package

    :expectedresults:
        1. Service down: package installation fail
        2. Service up: package installation successful
        3. VM down: package installation fail
        4. VM up: package installation successful

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_capsule_down():
    """Capsule service/VM down

    :id: 887f8172-e14f-11ea-9a77-4ceb42ab8dbc

    Steps:
        1. Stop capsule_1 service
        2. Try installing a package
        3. Start capsule_1 service and stop capsule_2 service
        4. Try installing a package.
        5. Start capsule_2 service. Power off capsule_1 vm
        6. Try installing a package
        7. Start capsule_1 vm. Power off capsule_2 vm
        8. Try installing a package
        9. Both capsules vm down
        10. Try installing a package
        11. Start both capsules

    :expectedresults:
        1. Package installation successful from capsule_2(see haproxy logs)
        2. Package installation successful from capsule_1(see haproxy logs)
        3. Package installation successful from capsule_2(see haproxy logs)
        4. Package installation successful from capsule_1(see haproxy logs)
        5. Package installation fail

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_remote_execution_on_client():
    """Remote Execution on client

    :id: e911acb4-e153-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Enable foreman-proxy-plugin-remote-execution-ssh on capsules
        2. Create ansible role and remote job, attach to the host(here client) and run the job

    :expectedresults:
        1. Ansible job is successful
        2. Remote job is successful

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_openscap_reporting():
    """openscap report to be uploaded

    :id: cfba6e54-e158-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Run `Puppet agent -t --noop`
        2. Run `foreman-scap-client <id>`

    :expectedresults:
        1. Should create openscap config file
        2. Should upload reports to sat
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_capsule_3():
    """Tests for capsule_3

    :id: 16fc8490-e15a-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Install capsule_3 and register as "The initial setup[5]".
        2. Unregister and remove katello-ca-consumer-latest. Re-register the client.
        3. Try package installation.
        4. Run `puppet agent -t -v`.
        5. Capsule_1 and capsule_2 service down.
        6. Capsule_1 and capsule_2 VM down.
        7. Capsule_1 and capsule_2 VM up.

    :expectedresults:
        1. Capsule_3 install successful
        2. Package installation is successful
        3. Scap reports upload to satellite should be served through capsule_3
        4. Request to be severed by capsule_3 when capsule_1 and capsule_2 service/VM are down.
        5. On starting the services/VM on down capsules, all the capsules including capsule_3
            should serve the client requests
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_multiclient():
    """Testing multiple clients to test the loadbalancer functionality

    :id: 8b59c69c-e15d-11ea-9a77-4ceb42ab8dbc

    :Steps: Use docker to spin new container client

    :expectedresults: All the clients(from docker) are registered to the capsules.

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_upgrade_the_setup():
    """Upgrading the setup previous GA to current snap

    :id: 64446c14-e15e-11ea-9a77-4ceb42ab8dbc

    :Steps:
        0. Create a setup from GA
        1. Sync new packages in the capsules content view
        2. Upgrade the satellite, upgrade the capsules.

    :expectedresults: The setup should works before and after the upgrade

    """
    pass
