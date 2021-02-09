"""CLI tests for logging.

:Requirement: Logging

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Logging

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
import re

import pytest
from fauxfactory import gen_string

from robottelo import manifests
from robottelo import ssh
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product_wait
from robottelo.cli.factory import make_repository
from robottelo.cli.subscription import Subscription
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


def line_count(file, connection=None):
    """Get number of lines in a file."""
    connection = connection or ssh.get_connection()
    result = connection.run(f'wc -l < {file}', output_format='plain')
    count = result.stdout.strip('\n')
    return count


def cut_lines(start_line, end_line, source_file, out_file, connection=None):
    """Given start and end line numbers, cut lines from source file
    and put them in out file."""
    connection = connection or ssh.get_connection()
    result = connection.run(
        'sed -n "{0},{1} p" {2} < {2} > {3}'.format(start_line, end_line, source_file, out_file)
    )
    return result


class SimpleLoggingTestCase(CLITestCase):
    """Test class for default logging to files."""

    org = None
    product = None

    @classmethod
    def setUpClass(cls):
        """Tests for logging to files"""
        super().setUpClass()

        # need own org for the manifest refresh test

        cls.org = make_org(cached=True)
        cls.product = make_product_wait({'organization-id': cls.org['id']})

    def _make_repository(self, options=None):
        """Makes a new repository and asserts its success"""
        if options is None:
            options = {}

        if not options.get('product-id'):
            options['product-id'] = self.product['id']

        return make_repository(options)

    @pytest.mark.tier4
    def test_positive_logging_from_foreman_core(self):
        """Check that GET command to Hosts API is logged and has request ID.

        :id: 0785260d-cb81-4351-a7cb-d7841335e2de

        :expectedresults: line of log with GET has request ID

        :CaseImportance: Medium
        """

        GET_line_found = False
        source_log = '/var/log/foreman/production.log'
        test_logfile = '/var/tmp/logfile_from_foreman_core'
        with ssh.get_connection() as connection:
            # get the number of lines in the source log before the test
            line_count_start = line_count(source_log, connection)
            # hammer command for this test
            result = connection.run('hammer host list')
            self.assertEqual(result.return_code, 0, "BASH command error?")
            # get the number of lines in the source log after the test
            line_count_end = line_count(source_log, connection)
            # get the log lines of interest, put them in test_logfile
            cut_lines(line_count_start, line_count_end, source_log, test_logfile, connection)
        # use same location on remote and local for log file extract
        ssh.download_file(test_logfile)
        # search the log file extract for the line with GET to host API
        with open(test_logfile) as logfile:
            for line in logfile:
                if re.search(r'Started GET \"\/api/hosts\?page=1', line):
                    self.logger.info('Found the line with GET to hosts API')
                    GET_line_found = True
                    # Confirm the request ID was logged in the line with GET
                    match = re.search(r'\[I\|app\|\w{8}\]', line)
                    assert match, "Request ID not found"
                    self.logger.info("Request ID found for logging from foreman core")
                    break
        assert GET_line_found, "The GET command to list hosts was not found in logs."

    @pytest.mark.tier4
    def test_positive_logging_from_foreman_proxy(self):
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
        with ssh.get_connection() as connection:
            # get the number of lines in the source logs before the test
            line_count_start_1 = line_count(source_log_1, connection)
            line_count_start_2 = line_count(source_log_2, connection)
            # hammer command for this test
            result = connection.run('hammer proxy refresh-features --id 1')
            self.assertEqual(result.return_code, 0, "BASH command error?")
            # get the number of lines in the source logs after the test
            line_count_end_1 = line_count(source_log_1, connection)
            line_count_end_2 = line_count(source_log_2, connection)
            # get the log lines of interest, put them in test_logfile_1
            cut_lines(
                line_count_start_1, line_count_end_1, source_log_1, test_logfile_1, connection
            )
            # get the log lines of interest, put them in test_logfile_2
            cut_lines(
                line_count_start_2, line_count_end_2, source_log_2, test_logfile_2, connection
            )
        # use same location on remote and local for log file extract
        ssh.download_file(test_logfile_1)
        # use same location on remote and local for log file extract
        ssh.download_file(test_logfile_2)
        # search the log file extract for the line with PUT to host API
        with open(test_logfile_1) as logfile:
            for line in logfile:
                if re.search(r'Started PUT \"\/api\/smart_proxies\/1\/refresh', line):
                    self.logger.info('Found the line with PUT to foreman proxy API')
                    PUT_line_found = True
                    # Confirm the request ID was logged in the line with PUT
                    match = re.search(r'\[I\|app\|\w{8}\]', line)
                    assert match, "Request ID not found"
                    self.logger.info("Request ID found for logging from foreman proxy")
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
                self.logger.info("Request ID also found in proxy.log")
                break

    @pytest.mark.tier4
    def test_positive_logging_from_candlepin(self):
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
        with ssh.get_connection() as connection:
            # get the number of lines in the source log before the test
            line_count_start = line_count(source_log, connection)
            # command for this test
            with manifests.clone() as manifest:
                upload_file(manifest.content, manifest.filename)
                Subscription.upload({'file': manifest.filename, 'organization-id': self.org['id']})
            # get the number of lines in the source log after the test
            line_count_end = line_count(source_log, connection)
            # get the log lines of interest, put them in test_logfile
            cut_lines(line_count_start, line_count_end, source_log, test_logfile, connection)
        # use same location on remote and local for log file extract
        ssh.download_file(test_logfile)
        # search the log file extract for the line with POST to candlepin API
        with open(test_logfile) as logfile:
            for line in logfile:
                if re.search(
                    r'verb=POST, uri=/candlepin/owners/{0}', line.format(self.org['name'])
                ):
                    self.logger.info('Found the line with POST to candlepin API')
                    POST_line_found = True
                    # Confirm the request ID was logged in the line with POST
                    match = re.search(regex, line)
                    assert match, "Request ID not found"
                    self.logger.info("Request ID found for logging from candlepin")
                    break
        assert POST_line_found, "The POST command to candlepin was not found in logs."

    @pytest.mark.tier4
    def test_positive_logging_from_dynflow(self):
        """Check POST to repositories API is logged while enabling a repo \
            and it has the request ID.

        :id: 2d1a5f64-0b1c-4f95-ad20-881134717c4c

        :expectedresults: line of log with POST has request ID

        :CaseImportance: Medium
        """

        POST_line_found = False
        source_log = '/var/log/foreman/production.log'
        test_logfile = '/var/tmp/logfile_dynflow'
        with ssh.get_connection() as connection:
            # get the number of lines in the source log before the test
            line_count_start = line_count(source_log, connection)
            # command for this test
            new_repo = self._make_repository({'name': gen_string('alpha')})
            self.logger.info(f"Created Repo {new_repo['name']} for dynflow log test")
            # get the number of lines in the source log after the test
            line_count_end = line_count(source_log, connection)
            # get the log lines of interest, put them in test_logfile
            cut_lines(line_count_start, line_count_end, source_log, test_logfile, connection)
        # use same location on remote and local for log file extract
        ssh.download_file(test_logfile)
        # search the log file extract for the line with POST to to repositories API
        with open(test_logfile) as logfile:
            for line in logfile:
                if re.search(r'Started POST \"/katello\/api\/repositories', line):
                    self.logger.info('Found the line with POST to repositories API.')
                    POST_line_found = True
                    # Confirm the request ID was logged in the line with POST
                    match = re.search(r'\[I\|app\|\w{8}\]', line)
                    assert match, "Request ID not found"
                    self.logger.info("Request ID found for logging from dynflow ")
        assert POST_line_found, "The POST command to enable a repo was not found in logs."
