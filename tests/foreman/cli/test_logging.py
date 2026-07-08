"""CLI tests for logging.

:Requirement: Logging

:CaseAutomation: Automated

:CaseComponent: Logging

:Team: Dragonfly

:CaseImportance: Medium

"""

import re

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import FOREMANCTL_PARAMETERS_FILE
from robottelo.logging import logger

pytestmark = pytest.mark.e2e


def cut_lines(start_line, end_line, source_file, out_file, host):
    """Given start and end line numbers, cut lines from source file
    and put them in out file."""
    return host.execute(
        f'sed -n "{start_line},{end_line} p" {source_file} < {source_file} > {out_file}'
    )


def test_positive_logging_from_foreman_core(target_sat):
    """Check that GET command to Hosts API is logged and has request ID.

    :id: 0785260d-cb81-4351-a7cb-d7841335e2de

    :expectedresults: line of log with GET has request ID

    :CaseImportance: Medium
    """

    GET_line_found = False
    source_log = '/var/log/foreman/production.log'
    test_logfile = '/var/tmp/logfile_from_foreman_core'
    # get the number of lines in the source log before the test
    line_count_start = target_sat.execute(f'wc -l < {source_log}').stdout.strip('\n')
    # hammer command for this test
    result = target_sat.execute('hammer host list')
    assert result.status == 0, f'Non-zero status for host list: {result.stderr}'
    # get the number of lines in the source log after the test
    line_count_end = target_sat.execute(f'wc -l < {source_log}').stdout.strip('\n')
    # get the log lines of interest, put them in test_logfile
    cut_lines(line_count_start, line_count_end, source_log, test_logfile, target_sat)
    # use same location on remote and local for log file extract
    target_sat.get(remote_path=test_logfile)
    # search the log file extract for the line with GET to host API
    with open(test_logfile) as logfile:
        for line in logfile:
            if re.search(r'Started GET \"\/api/hosts\?page=1', line):
                logger.info('Found the line with GET to hosts API')
                GET_line_found = True
                # Confirm the request ID was logged in the line with GET
                match = re.search(r'\[I\|app\|\w{8}\]', line)
                assert match, "Request ID not found"
                logger.info("Request ID found for logging from foreman core")
                break
    assert GET_line_found, "The GET command to list hosts was not found in logs."


def test_positive_logging_from_foreman_proxy(target_sat):
    """Check PUT to Smart Proxy API to refresh the features is logged and has request ID.

    :id: 0ecd8406-6cf1-4520-b8b6-8a164a1e60c2

    :expectedresults: line of log with PUT has request ID

    :CaseImportance: Medium
    """

    PUT_line_found = False
    request_id = None
    source_log_1 = '/var/log/foreman/production.log'
    test_logfile_1 = '/var/tmp/logfile_1_from_proxy'
    source_log_2 = '/var/log/foreman-proxy/proxy.log'
    test_logfile_2 = '/var/tmp/logfile_2_from_proxy'
    # get the number of lines in the source logs before the test
    line_count_start_1 = target_sat.execute(f'wc -l < {source_log_1}').stdout.strip('\n')
    line_count_start_2 = target_sat.execute(f'wc -l < {source_log_2}').stdout.strip('\n')
    # hammer command for this test
    result = target_sat.execute('hammer proxy refresh-features --id 1')
    assert result.status == 0, f'Non-zero status for host list: {result.stderr}'
    # get the number of lines in the source logs after the test
    line_count_end_1 = target_sat.execute(f'wc -l < {source_log_1}').stdout.strip('\n')
    line_count_end_2 = target_sat.execute(f'wc -l < {source_log_2}').stdout.strip('\n')
    # get the log lines of interest, put them in test_logfile_1
    cut_lines(line_count_start_1, line_count_end_1, source_log_1, test_logfile_1, target_sat)
    # get the log lines of interest, put them in test_logfile_2
    cut_lines(line_count_start_2, line_count_end_2, source_log_2, test_logfile_2, target_sat)
    # use same location on remote and local for log file extract
    target_sat.get(remote_path=test_logfile_1)
    # use same location on remote and local for log file extract
    target_sat.get(remote_path=test_logfile_2)
    # search the log file extract for the line with PUT to host API
    with open(test_logfile_1) as logfile:
        for line in logfile:
            if re.search(r'Started PUT \"\/api\/smart_proxies\/1\/refresh', line):
                logger.info('Found the line with PUT to foreman proxy API')
                PUT_line_found = True
                # Confirm the request ID was logged in the line with PUT
                match = re.search(r'\[I\|app\|\w{8}\]', line)
                assert match, "Request ID not found"
                logger.info("Request ID found for logging from foreman proxy")
                p = re.compile(r"\w{8}")
                result = p.search(line)
                request_id = result.group(0)
                break
    assert PUT_line_found, "The PUT command to refresh proxies was not found in logs."
    # search the local copy of proxy.log file for the same request ID
    with open(test_logfile_2) as logfile:
        for line in logfile:
            # Confirm request ID was logged in proxy.log
            match = line.find(request_id)
            assert match, "Request ID not found in proxy.log"
            logger.info("Request ID also found in proxy.log")
            break


def test_positive_logging_from_candlepin(module_org, module_sca_manifest, target_sat):
    """Check logging after manifest upload.

    :id: 8c06e501-52d7-4baf-903e-7de9caffb066

    :expectedresults: line of logs with POST has request ID

    :CaseImportance: Medium
    """

    POST_line_found = False
    source_log = '/var/log/candlepin/candlepin.log'
    test_logfile = '/var/tmp/logfile_from_candlepin'
    # regex for a version 4 UUID (8-4-4-12 format)
    regex = r"\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b"
    # get the number of lines in the source log before the test
    line_count_start = target_sat.execute(f'wc -l < {source_log}').stdout.strip('\n')
    # command for this test
    with module_sca_manifest as manifest:
        target_sat.upload_manifest(module_org.id, manifest, interface='CLI')
    # get the number of lines in the source log after the test
    line_count_end = target_sat.execute(f'wc -l < {source_log}').stdout.strip('\n')
    # get the log lines of interest, put them in test_logfile
    cut_lines(line_count_start, line_count_end, source_log, test_logfile, target_sat)
    # use same location on remote and local for log file extract
    target_sat.get(remote_path=test_logfile)
    # search the log file extract for the line with POST to candlepin API
    with open(test_logfile) as logfile:
        for line in logfile:
            if re.search(r'verb=POST, uri=/candlepin/owners/{0}', line.format(module_org.name)):
                logger.info('Found the line with POST to candlepin API')
                POST_line_found = True
                # Confirm the request ID was logged in the line with POST
                match = re.search(regex, line)
                assert match, "Request ID not found"
                logger.info("Request ID found for logging from candlepin")
                break
    assert POST_line_found, "The POST command to candlepin was not found in logs."


def test_positive_logging_from_dynflow(module_org, target_sat):
    """Check POST to repositories API is logged while enabling a repo \
        and it has the request ID.

    :id: 2d1a5f64-0b1c-4f95-ad20-881134717c4c

    :expectedresults: line of log with POST has request ID

    :CaseImportance: Medium
    """

    POST_line_found = False
    source_log = '/var/log/foreman/production.log'
    test_logfile = '/var/tmp/logfile_dynflow'
    product = target_sat.api.Product(organization=module_org).create()
    repo_name = gen_string('alpha')
    # get the number of lines in the source log before the test
    line_count_start = target_sat.execute(f'wc -l < {source_log}').stdout.strip('\n')
    # command for this test
    new_repo = target_sat.api.Repository(name=repo_name, product=product).create()
    logger.info(f'Created Repo {new_repo.name} for dynflow log test')
    # get the number of lines in the source log after the test
    line_count_end = target_sat.execute(f'wc -l < {source_log}').stdout.strip('\n')
    # get the log lines of interest, put them in test_logfile
    cut_lines(line_count_start, line_count_end, source_log, test_logfile, target_sat)
    # use same location on remote and local for log file extract
    target_sat.get(remote_path=test_logfile)
    # search the log file extract for the line with POST to to repositories API
    with open(test_logfile) as logfile:
        for line in logfile:
            if re.search(r'Started POST \"/katello\/api\/v2\/repositories', line):
                logger.info('Found the line with POST to repositories API.')
                POST_line_found = True
                # Confirm the request ID was logged in the line with POST
                match = re.search(r'\[I\|app\|\w{8}\]', line)
                assert match, "Request ID not found"
                logger.info("Request ID found for logging from dynflow ")
    assert POST_line_found, "The POST command to enable a repo was not found in logs."


def test_positive_logging_from_pulp3(module_org, target_sat):
    """
    Verify Pulp3 logs are getting captured using pulp3 correlation ID

    :id: 8d5718e6-3442-47d6-b541-0aa78d007e8b

    :CaseImportance: High
    """
    source_log = '/var/log/foreman/production.log'
    test_logfile = '/var/log/messages'

    # Create custom product and repository
    product_name = gen_string('alpha')
    name = product_name
    label = product_name
    desc = product_name
    product = target_sat.cli_factory.make_product(
        {'description': desc, 'label': label, 'name': name, 'organization-id': module_org.id},
    )
    repo = target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product['id'],
            'url': settings.repos.yum_0.url,
        },
    )
    # Synchronize the repository
    target_sat.cli.Product.synchronize({'id': product['id'], 'organization-id': module_org.id})
    target_sat.cli.Repository.synchronize({'id': repo['id']})
    # Get the id of repository sync from task
    task_out = target_sat.execute(
        f"hammer task list | grep -F 'Synchronize repository' | grep -F {product_name}"
    ).stdout.splitlines()[0][:8]
    prod_log_out = target_sat.execute(f'grep  {task_out} {source_log}').stdout.splitlines()[0]
    # Get correlation id of pulp from production logs
    pulp_correlation_id = re.search(r'\[I\|bac\|\w{8}\]', prod_log_out).group()[7:15]
    # verify pulp correlation id in message
    message_log = target_sat.execute(f'cat {test_logfile} | grep {pulp_correlation_id}')
    assert message_log.status == 0


@pytest.mark.foremanctl
class TestSOSReportForemanctl:
    """Tests for the foremanctl sos plugin on containerized Satellite."""

    SOS_CMD = 'sos report -o foremanctl --batch --tmp-dir /var/tmp'
    EXTRACT_DIR = '/var/tmp/sosreport-extract'

    @pytest.fixture(scope="module")
    def sosreport_extract(self, module_target_sat):
        """Run sosreport and yield the extracted report directory path."""
        result = module_target_sat.execute(self.SOS_CMD, timeout='10m')
        assert result.status == 0, f'sosreport failed:\n{result.stdout}\n{result.stderr}'

        tarball = module_target_sat.execute(
            'ls /var/tmp/sosreport-*.tar.xz | head -1'
        ).stdout.strip()
        assert tarball, 'No sosreport tarball found'

        module_target_sat.execute(f'mkdir -p {self.EXTRACT_DIR}')
        module_target_sat.execute(f'tar xf {tarball} -C {self.EXTRACT_DIR}')

        report_dir = module_target_sat.execute(
            f'ls -d {self.EXTRACT_DIR}/sosreport-*'
        ).stdout.strip()
        yield report_dir
        module_target_sat.execute(f'rm -rf /var/tmp/sosreport-* {self.EXTRACT_DIR}')

    def test_positive_sosreport_foremanctl_collects_data(
        self, module_target_sat, sosreport_extract
    ):
        """Verify the foremanctl sos plugin activates on a containerized
        Satellite and collects expected configuration files and command output.

        :id: dc91bb91-d785-49f9-b19d-b0484662ce3f

        :steps:
            1. Run sosreport with the foremanctl plugin
            2. Verify foremanctl configuration files are collected
            3. Verify foremanctl command outputs are collected

        :expectedresults:
            1. parameters.yaml and inventory files are present in the report
            2. foremanctl features and foremanctl health output are collected
        """
        report = sosreport_extract

        params = module_target_sat.execute(f'test -f {report}/var/lib/foremanctl/parameters.yaml')
        assert params.status == 0, 'parameters.yaml not collected'

        inventory = module_target_sat.execute(f'test -f {report}/etc/foremanctl/inventory')
        assert inventory.status == 0, 'foremanctl inventory not collected'

        features = module_target_sat.execute(
            f'test -f {report}/sos_commands/foremanctl/foremanctl_features'
        )
        assert features.status == 0, 'foremanctl features output not collected'

        health = module_target_sat.execute(
            f'test -f {report}/sos_commands/foremanctl/foremanctl_health'
        )
        assert health.status == 0, 'foremanctl health output not collected'

    def test_positive_sosreport_foremanctl_scrub_sensitive_values(
        self, module_target_sat, sosreport_extract
    ):
        """Verify the foremanctl sos plugin scrubs sensitive credentials
        from parameters.yaml and foremanctl log files while preserving
        non-sensitive values.

        :id: a8bdb8f7-dd0f-44ee-9722-af4b1815aad2

        :steps:
            1. Verify passwords exist in the original parameters.yaml
            2. Run sosreport with the foremanctl plugin
            3. Check password values in parameters.yaml are scrubbed
            4. Check non-sensitive values are NOT scrubbed
            5. Verify foremanctl log files are collected
            6. Check that sensitive values in logs are scrubbed

        :expectedresults:
            1. All password values in parameters.yaml are scrubbed
            2. Non-sensitive values like database names remain intact
            3. foremanctl log files are present in the report
            4. Any lines matching sensitive value patterns in logs
               have their values scrubbed'
        """
        # only password exists for now on the default deploy and more can be added in future
        SENSITIVE_KEYWORD = ('password',)
        SCRUB_MARKER = '***'

        original = module_target_sat.execute(f'grep -i password {FOREMANCTL_PARAMETERS_FILE}')
        assert original.stdout.strip(), f'No password entries found in {FOREMANCTL_PARAMETERS_FILE}'

        report = sosreport_extract

        # Verify parameters.yaml scrubbing
        collected = module_target_sat.execute(f'cat {report}/var/lib/foremanctl/parameters.yaml')
        assert collected.status == 0, 'Could not read collected parameters.yaml'

        for keyword in SENSITIVE_KEYWORD:
            matching_lines = [
                line for line in collected.stdout.splitlines() if keyword in line.lower()
            ]
            for line in matching_lines:
                assert SCRUB_MARKER in line, f'Sensitive value not scrubbed in line: {line}'

        # Verify log file scrubbing
        log_dir = f'{report}/var/log/foremanctl'
        log_files = module_target_sat.execute(f'ls {log_dir}/foremanctl*log* 2>/dev/null')
        assert log_files.status == 0, 'Failed to list foremanctl log files in sosreport'

        sensitive_check = module_target_sat.execute(
            f'grep -hEi "passw|cred|token|secret" {log_dir}/foremanctl*log* 2>/dev/null'
        )
        if sensitive_check.stdout.strip():
            for line in sensitive_check.stdout.splitlines():
                assert SCRUB_MARKER in line, f'Sensitive value not scrubbed in log line: {line}'
