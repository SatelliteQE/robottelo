import logging
import re

import requests
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from robottelo.config import settings

LOGGER = logging.getLogger('robottelo')
launch_types = ['satellite6', 'upgrades']


class ReportPortal:
    """Represents ReportPortal

    This holds the properties and functions to interact with Report Portal properties and launches
    """

    defect_types = {
        'product_bug': 'PB001',
        'rhel_bug': 'pb_1ies7k2sxbsdh',
        'satellite_bug': 'pb_vf6zbvnxv77d',
        'automation_bug': 'AB001',
        'robottelo_bug': 'ab_1ibec4rs6jf3r',
        'nailgun_bug': 'ab_t4kkyw0yaaet',
        'airgun_bug': 'ab_u7umbjyvti7a',
        'system_issue': 'SI001',
        'zalenium_issue': 'si_rhufdawx03e8',
        'to_investigate': 'TI001',
        'no_defect': 'ND001',
    }
    statuses = ['failed', 'passed', 'skipped', 'interrupted', 'in_progress']

    def __init__(self):
        """Configure the settings and initiate report portal properties"""
        if not settings.configured:
            settings.configure()
        self.rp_url = settings.report_portal.portal_url
        self.rp_project = settings.report_portal.project
        self.rp_api_key = settings.report_portal.api_key

    @property
    def api_url(self):
        """Super url of report portal
        :returns: Base url for API request
        """
        return f'{self.rp_url}/api/v1/{self.rp_project}'

    @property
    def headers(self):
        """The headers for Report Portal Requests.
        :returns: header for API request
        """
        return {'Authorization': f'Bearer {self.rp_api_key}'}

    def _format_launches(self, launches):
        """The pretty formatter function that formats launches in a structured way

        :param filter launches: Satellite or Upgrade Type launches

        :returns dict: Launches, keyed with their snap_versions formatted as,
            `{'snap_version1':launch_object1, 'snap_version2': launch_object2}`
        """
        formatted_launches = {}
        for launch_info in launches:
            launch = Launch(rp=self, launch_info=launch_info)
            if hasattr(launch, 'satellite_version'):
                sat_ver = launch.satellite_version
                snap_dict = {launch.snap_version: launch}
                if sat_ver not in formatted_launches:
                    formatted_launches[sat_ver] = snap_dict
                else:
                    formatted_launches[sat_ver].update(snap_dict)
        return formatted_launches

    def _launch_requester(self):
        """The launch GET requester to fetch the all available launches of ReportPortal

        :returns dict: The json of all RP launches
        """
        params = {'page.page': 1, 'page.size': 500, 'page.sort': 'startTime'}
        resp = requests.get(
            url=f'{self.api_url}/launch', headers=self.headers, params=params, verify=False
        )
        resp.raise_for_status()
        return resp.json()

    def launches(self, sat_version=None, launch_type='satellite6'):
        """Returns launches in Report Portal customized by sat_version, launch_type and
        latest number of launches sorted by latest sat version/snap version.

        This does not includes each tests data for all tests in all launches, but it includes
        just an overview data for all and each launch in Report Portal

        :param str sat_version: The satellite version
            If its not specified, then latest count of launches of satellite versions returned
        :param str launch_type: Either satellite6 or upgrades,
            default returns only non-upgrade launches
        :returns dict: The launches of Report portal.
            if sat_version is given,
            ```{'snap_version1':launch_object1, 'snap_version2':launch_object2}```
            else,
            ```{'sat_version1':{'snap_version1':launch_object1, ..}, 'sat_version2':{}}```
        """
        if launch_type not in launch_types:
            raise ValueError(
                f'Wrong Launch Type is given as {launch_type} should be one of {launch_types}'
            )
        data = self._launch_requester()
        sorted_launches = sorted(
            data['content'], key=lambda launch: launch['startTime'], reverse=True
        )
        typed_launches = filter(
            lambda launch: launch['name'].lower() == launch_type, sorted_launches
        )
        launches_ = self._format_launches(typed_launches)
        if sat_version:
            if sat_version not in launches_:
                raise ValueError(
                    f'The given satellite version \'{sat_version}\' is not available in '
                    f'Report portal project \'{self.rp_project}\''
                )
            else:
                return launches_[sat_version]
        return launches_

    def launch(self, sat_version, snap_version=None, launch_type='satellite6'):
        """Returns a specific launch data in Report Portal Project

        This does not includes each tests data in launch

        :param str sat_version: The satellite version
        :param str snap_version: The snap version of a given satellite version
            if None, the latest launch data of a given sat_version is returned
        :param str launch_type: Either satellite6 or upgrades, default returns only
            non-upgrade launches
        :returns dict: The data directory of requested or latest launch
        """
        launches_ = self.launches(sat_version=sat_version, launch_type=launch_type)
        if snap_version:
            if snap_version not in launches_.keys():
                raise ValueError(
                    f'The given snap_version \'{snap_version}\' is not available '
                    f'in satellite version \'{sat_version}\''
                )
        else:
            # Get the latest launch of the given sat_version
            snap_version = next(iter(launches_.keys()))
        return launches_[snap_version]


class Launch:
    def __init__(self, rp, launch_info):
        """Initiates the Launch and its properties of a specified snap version in
        a specified satellite version

        :param ReportPortal rp: A report portal object
        :param dict launch_info: The dict information about a launch
        """
        self.report_portal = rp
        self.info = launch_info
        self.name = self.info['name']
        self.statistics = self.info['statistics']['executions']
        self._versions()

    def _versions(self):
        """Sets satellite and snap version attributes of a launch"""
        version_compiler = re.compile(r'([\d\.]+)[\.-](\d+\.\d|[A-Z]+)')
        if not self.info['attributes']:
            LOGGER.debug(
                'Launch with no launch_attributes is detected. '
                'This will be removed from launch collection.'
            )
            return
        launch_attrs = [
            self.info['attributes'][attr]['value'] for attr in range(len(self.info['attributes']))
        ]
        try:
            launch_name = next(filter(version_compiler.search, launch_attrs))
        except StopIteration:
            LOGGER.debug(
                'Launch with no build name in launch_attributes is detected. '
                f'The launch has tags {launch_attrs}'
            )
            return
        self.satellite_version = re.search(version_compiler, launch_name).group(1)
        self.snap_version = re.search(version_compiler, launch_name).group(2)

    def _test_params(self, status, defect_type, user):
        """Customise parameters for Test items API request

        :returns dict: The parameters dict for API test items request
        """
        params = [
            ('filter.eq.launchId', self.info['id']),
            ('page.page', 1),
            ('page.size', 50),
            ('page.sort', 'startTime'),
        ]
        rp_defect_types = ReportPortal.defect_types
        if defect_type:
            if defect_type in rp_defect_types:
                params.insert(0, ('filter.eq.issueType', rp_defect_types[defect_type].lower()))
            else:
                raise ValueError(
                    f'Invalid value \'{defect_type}\' for defect type parameter, '
                    f'should be one of {[*rp_defect_types.keys()]}'
                )
        rp_statuses = ReportPortal.statuses
        if status:
            if status in rp_statuses:
                params.insert(2, ('filter.eq.status', status))
            else:
                raise ValueError(
                    f'Invalid value \'{status}\' for status parameter, '
                    f'should be one of {rp_statuses}'
                )
        if user:
            params.insert(0, ('filter.has.attributeKey', 'case_owner'))
            params.insert(1, ('filter.has.attributeValue', user))
        return dict(params)

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_fixed(10),
    )
    def _test_requester(self, params, page):
        """The Test Items GET requester to fetch the data on a page

        If any error and before Failing explicitly, it retries for 3 times with 10 seconds delay

        :returns tuple (int, list): Total pages count and the list of tests along with
            each tests properties in a page
        """
        params['page.page'] = page
        resp = requests.get(
            url=f'{self.report_portal.api_url}/item',
            headers=self.report_portal.headers,
            params=params,
            verify=False,
        )
        resp.raise_for_status()
        total_pages = resp.json()['page']['totalPages']
        pagedata = resp.json().get('content')
        return total_pages, pagedata

    def tests(self, status=None, defect_type=None, user=None):
        """Returns tests data customized by kwargs parameters.

        This is a main function that will be called to retrieve the tests data
        of a particular test status or/and defect_type

        :param str status: Filter tests of a launch with tests `status`
        :param str defect_type: Filter tests of a launch with tests `defect_type`
        :returns dict: All filtered tests dict based on params data keyed by test name and test
            properties as value, in format -
            ```{'test_name1':test1_properties_dict, 'test_name2':test2_properties_dict}```
        """
        page = 1
        params = self._test_params(status, defect_type, user)
        total_pages, data = self._test_requester(params=params, page=page)
        while page < total_pages:
            page += 1
            _, pagedata = self._test_requester(params=params, page=page)
            data.extend(pagedata)
        # formatting tests data to return tests data keyed by test name
        tests_ = {test['name']: test for test in data}
        return tests_
