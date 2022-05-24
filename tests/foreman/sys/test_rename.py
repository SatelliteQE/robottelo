"""Test class for ``katello-change-hostname``

:Requirement: katello-change-hostname

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: satellite-change-hostname

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
import pytest
from fauxfactory import gen_string

from robottelo.cli import hammer
from robottelo.config import settings

BCK_MSG = "**** Hostname change complete! ****"
BAD_HN_MSG = (
    "{0} is not a valid fully qualified domain name. Please use a valid FQDN and try again."
)
NO_CREDS_MSG = "Username and/or Password options are missing!"
BAD_CREDS_MSG = "There is a problem with the credentials"


@pytest.mark.run_in_one_thread
@pytest.mark.destructive
class TestRenameHost:
    """Implements ``katello-change-hostname`` tests"""

    @pytest.mark.skip_if_open("BZ:1925616")
    @pytest.mark.destructive
    def test_positive_rename_satellite(self, module_org, module_product, target_sat):
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
        old_hostname = target_sat.execute('hostname').stdout.strip()
        new_hostname = f'new-{old_hostname}'
        # create installation medium with hostname in path
        medium_path = f'http://{old_hostname}/testpath-{gen_string("alpha")}/os/'
        medium = target_sat.api.Media(organization=[module_org], path_=medium_path).create()
        repo = target_sat.api.Repository(product=module_product, name='testrepo').create()
        result = target_sat.execute(
            f'satellite-change-hostname {new_hostname} -y -u {username} -p {password}',
            timeout=1200000,
        )
        assert result.status == 0, 'unsuccessful rename'
        assert BCK_MSG in result.stdout
        # services running after rename?
        result = target_sat.execute('hammer ping')
        assert result.status == 0, 'services did not start properly'
        # basic hostname check
        result = target_sat.execute('hostname')
        assert result.status == 0
        assert new_hostname in result.stdout, 'hostname left unchanged'
        # check default capsule
        result = target_sat.execute(
            f'hammer -u {username} -p {password} --output json capsule info --name {new_hostname}'
        )
        assert result.status == 0, 'internal capsule not renamed correctly'
        assert hammer.parse_json(result.stdout)['url'] == f"https://{new_hostname}:9090"
        # check old consumer certs were deleted
        result = target_sat.execute(f'rpm -qa | grep ^{old_hostname}')
        assert result.status == 1, 'old consumer certificates not removed'
        # check new consumer certs were created
        result = target_sat.execute(f'rpm -qa | grep ^{new_hostname}')
        assert result.status == 0, 'new consumer certificates not created'
        # check if installation media paths were updated
        result = target_sat.execute(
            f'hammer -u {username} -p {password} --output json medium info --id {medium.id}'
        )
        assert result.status == 0
        assert new_hostname in hammer.parse_json(result.stdout)['path']
        # check answer file for instances of old hostname
        ans_f = '/etc/foreman-installer/scenarios.d/satellite-answers.yaml'
        result = target_sat.execute(f'grep " {old_hostname}" {ans_f}')
        assert result.status == 1, 'old hostname was not correctly replaced in answers.yml'

        # check repository published at path
        result = target_sat.execute(
            f'hammer -u {username} -p {password} --output json repository info --id {repo.id}'
        )
        assert result.status == 0
        assert (
            new_hostname in hammer.parse_json(result.stdout)['published-at']
        ), 'repository published path not updated correctly'

        # check for any other occurences of old hostname
        result = target_sat.execute(f'grep " {old_hostname}" /etc/* -r')
        assert result.status == 1, 'there are remaining instances of the old hostname'

        repo.sync()
        cv = target_sat.api.ContentView(organization=module_org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()

    @pytest.mark.destructive
    def test_negative_rename_sat_to_invalid_hostname(self, target_sat):
        """change to invalid hostname on Satellite server

        :id: 385fad60-3990-42e0-9436-4ebb71918125

        :BZ: 1485884

        :expectedresults: script terminates with a message, hostname
            is not changed

        :CaseAutomation: Automated
        """
        username = settings.server.admin_username
        password = settings.server.admin_password
        original_name = target_sat.hostname
        hostname = gen_string('alpha')
        result = target_sat.execute(
            f'satellite-change-hostname -y {hostname} -u {username} -p {password}'
        )
        assert result.status == 1
        assert BAD_HN_MSG.format(hostname) in result.stdout
        # assert no changes were made
        result = target_sat.execute('hostname')
        assert original_name == result.stdout.strip(), "Invalid hostame assigned"

    @pytest.mark.destructive
    def test_negative_rename_sat_no_credentials(self, target_sat):
        """change hostname without credentials on Satellite server

        :id: ed4f7611-33c9-455f-8557-507cc59ede92

        :BZ: 1485884

        :expectedresults: script terminates with a message, hostname
            is not changed

        :CaseAutomation: Automated
        """
        original_name = target_sat.hostname
        hostname = gen_string('alpha')
        result = target_sat.execute(f'satellite-change-hostname -y {hostname}')
        assert result.status == 1
        assert NO_CREDS_MSG in result.stdout
        # assert no changes were made
        result = target_sat.execute('hostname')
        assert original_name == result.stdout.strip(), "Invalid hostame assigned"

    @pytest.mark.skip_if_open("BZ:1925616")
    @pytest.mark.destructive
    def test_negative_rename_sat_wrong_passwd(self, target_sat):
        """change hostname with wrong password on Satellite server

        :id: e6d84c5b-4bb1-4400-8022-d01cc9216936

        :BZ: 1485884, 1897360, 1925616

        :expectedresults: script terminates with a message, hostname
            is not changed

        :CaseAutomation: Automated
        """
        username = settings.server.admin_username
        original_name = target_sat.hostname
        new_hostname = f'new-{original_name}'
        password = gen_string('alpha')
        result = target_sat.execute(
            f'satellite-change-hostname -y {new_hostname} -u {username} -p {password}'
        )
        assert result.status == 1
        assert BAD_CREDS_MSG in result.stderr

    @pytest.mark.stubbed
    @pytest.mark.destructive
    def test_positive_rename_capsule(self, target_sat):
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
        result = target_sat.execute(
            'satellite-change-hostname '
            f'-y -u {username} -p {password} '
            '--disable-system-checks '
            f'--scenario capsule {hostname}'
        )
        assert result.status == 0
        assert BCK_MSG in result.stdout
