"""Test class for ``katello-change-hostname``

:Requirement: katello-change-hostname

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Platform

:CaseImportance: High

"""
from fauxfactory import gen_string
import pytest

from robottelo.cli import hammer
from robottelo.config import settings
from robottelo.constants import SATELLITE_ANSWER_FILE

BCK_MSG = "**** Hostname change complete! ****"
BAD_HN_MSG = (
    "{0} is not a valid fully qualified domain name. Please use a valid FQDN and try again."
)
NO_CREDS_MSG = "Username and/or Password options are missing!"
BAD_CREDS_MSG = "Unable to authenticate user admin"
pytestmark = pytest.mark.destructive


@pytest.mark.e2e
def test_positive_rename_satellite(module_org, module_product, module_target_sat):
    """run katello-change-hostname on Satellite server

    :id: 9944bfb1-1440-4820-ada8-2e219f09c0be

    :setup: Satellite server with synchronized rh and custom
        repos and with a registered host

    :steps:

        1. Rename Satellite using katello-change-hostname
        2. Do basic checks for hostname change (hostnamctl)
        3. Run some existence tests, as in backup testing
        4. Verify certificates were properly recreated, check
            for instances of old hostname
            in etc/foreman-installer/scenarios.d/
        5. Check for updated repo urls, installation media paths,
            updated internal capsule
        6. Check usability of entities created before rename:
            resync repos, republish CVs and re-register hosts
        7. Create new entities (run end-to-end test from robottelo)

    :BZ: 1469466, 1897360, 1925616

    :expectedresults: Satellite hostname is successfully updated
        and the server functions correctly

    :CaseImportance: Critical

    :CaseAutomation: Automated
    """
    username = settings.server.admin_username
    password = settings.server.admin_password
    old_hostname = module_target_sat.execute('hostname').stdout.strip()
    new_hostname = f'new-{old_hostname}'
    # create installation medium with hostname in path
    medium_path = f'http://{old_hostname}/testpath-{gen_string("alpha")}/os/'
    medium = module_target_sat.api.Media(organization=[module_org], path_=medium_path).create()
    repo = module_target_sat.api.Repository(product=module_product, name='testrepo').create()
    # create /etc/hosts entry to pass s-c-h validation
    sat_ip = module_target_sat.execute(
        "ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1"
    ).stdout.strip()
    module_target_sat.execute(f'echo "{sat_ip} {old_hostname} {new_hostname}" >> /etc/hosts')
    result = module_target_sat.execute(
        f'satellite-change-hostname {new_hostname} -y -u {username} -p {password}',
        timeout=1200000,
    )
    assert result.status == 0, 'unsuccessful rename'
    assert BCK_MSG in result.stdout
    # services running after rename?
    result = module_target_sat.execute('hammer ping')
    assert result.status == 0, 'services did not start properly'
    # basic hostname check
    result = module_target_sat.execute('hostname')
    assert result.status == 0
    assert new_hostname in result.stdout, 'hostname left unchanged'
    # check default capsule
    result = module_target_sat.execute(
        f'hammer -u {username} -p {password} --output json capsule info --name {new_hostname}'
    )
    assert result.status == 0, 'internal capsule not renamed correctly'
    assert hammer.parse_json(result.stdout)['url'] == f"https://{new_hostname}:9090"

    # check if installation media paths were updated
    result = module_target_sat.execute(
        f'hammer -u {username} -p {password} --output json medium info --id {medium.id}'
    )
    assert result.status == 0
    assert new_hostname in hammer.parse_json(result.stdout)['path']
    # check answer file for instances of old hostname
    result = module_target_sat.execute(f'grep " {old_hostname}" {SATELLITE_ANSWER_FILE}')
    assert result.status == 1, 'old hostname was not correctly replaced in answers.yml'

    # check repository published at path
    result = module_target_sat.execute(
        f'hammer -u {username} -p {password} --output json repository info --id {repo.id}'
    )
    assert result.status == 0
    assert (
        new_hostname in hammer.parse_json(result.stdout)['published-at']
    ), 'repository published path not updated correctly'

    # check for any other occurences of old hostname
    result = module_target_sat.execute(f'grep " {old_hostname}" --exclude-dir="promtail" /etc/* -r')
    assert result.status != 0, 'there are remaining instances of the old hostname'

    repo.sync()
    cv = module_target_sat.api.ContentView(organization=module_org).create()
    cv.repository = [repo]
    cv.update(['repository'])
    cv.publish()


def test_negative_rename_sat_to_invalid_hostname(module_target_sat):
    """change to invalid hostname on Satellite server

    :id: 385fad60-3990-42e0-9436-4ebb71918125

    :BZ: 1485884

    :expectedresults: script terminates with a message, hostname
        is not changed

    :CaseAutomation: Automated
    """
    username = settings.server.admin_username
    password = settings.server.admin_password
    original_name = module_target_sat.execute('hostname').stdout.strip()
    hostname = gen_string('alpha')
    result = module_target_sat.execute(
        f'satellite-change-hostname -y {hostname} -u {username} -p {password}'
    )
    assert result.status == 1
    assert BAD_HN_MSG.format(hostname) in result.stdout
    # assert no changes were made
    result = module_target_sat.execute('hostname')
    assert original_name == result.stdout.strip(), "Invalid hostame assigned"


def test_negative_rename_sat_no_credentials(module_target_sat):
    """change hostname without credentials on Satellite server

    :id: ed4f7611-33c9-455f-8557-507cc59ede92

    :BZ: 1485884

    :expectedresults: script terminates with a message, hostname
        is not changed

    :CaseAutomation: Automated
    """
    original_name = module_target_sat.execute('hostname').stdout.strip()
    hostname = gen_string('alpha')
    result = module_target_sat.execute(f'satellite-change-hostname -y {hostname}')
    assert result.status == 1
    assert NO_CREDS_MSG in result.stdout
    # assert no changes were made
    result = module_target_sat.execute('hostname')
    assert original_name == result.stdout.strip(), "Invalid hostame assigned"


def test_negative_rename_sat_wrong_passwd(module_target_sat):
    """change hostname with wrong password on Satellite server

    :id: e6d84c5b-4bb1-4400-8022-d01cc9216936

    :BZ: 1485884, 1897360, 1925616

    :expectedresults: script terminates with a message, hostname
        is not changed

    :CaseAutomation: Automated
    """
    username = settings.server.admin_username
    original_name = module_target_sat.execute('hostname').stdout.strip()
    new_hostname = f'new-{original_name}'
    password = gen_string('alpha')
    result = module_target_sat.execute(
        f'satellite-change-hostname -y {new_hostname} -u {username} -p {password}'
    )
    assert result.status == 1
    assert BAD_CREDS_MSG in result.stderr[1].decode()


@pytest.mark.stubbed
def test_positive_rename_capsule(module_target_sat):
    """run katello-change-hostname on Capsule

    :id: 4aa9fd86-bba9-49e4-a67a-8685e1ab5a74

    :setup: Capsule server registered to Satellite, with common features
        enabled, with synchronized content and a host registered to it

    :steps:
        1. Rename Satellite using katello-change-hostname
        2. Do basic checks for hostname change (hostnamctl)
        3. Verify certificates were properly recreated, check
            for instances of old hostname
            in etc/foreman-installer/scenarios.d/
        4. Re-register Capsule to Satellite, resync content
        5. Re-register old host, register new one to Satellite,
        6. Check hosts can consume content, run basic REX command,
            import Puppet environments from hosts

    :BZ: 1469466, 1473614

    :expectedresults: Capsule hostname is successfully updated
        and the capsule fuctions correctly

    :CaseAutomation: Automated
    """
    # Save original hostname, get credentials, eventually will
    # end up in setUpClass
    username = settings.server.admin_username
    password = settings.server.admin_password
    # the rename part of the test, not necessary to run from robottelo
    hostname = gen_string('alpha')
    result = module_target_sat.execute(
        'satellite-change-hostname '
        f'-y -u {username} -p {password} '
        '--disable-system-checks '
        f'--scenario capsule {hostname}'
    )
    assert result.status == 0
    assert BCK_MSG in result.stdout
