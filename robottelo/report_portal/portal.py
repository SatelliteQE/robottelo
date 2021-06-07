import requests
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from robottelo.config import settings
from robottelo.logging import logger


class ReportPortal:
    """Represents ReportPortal

    This holds the properties and functions to interact with Report Portal properties and launches
    """

    defect_types = {
        'product_bug': 'pb001',
        'rhel_bug': 'pb_1ies7k2sxbsdh',
        'satellite_bug': 'pb_vf6zbvnxv77d',
        'automation_bug': 'ab001',
        'robottelo_bug': 'ab_1ibec4rs6jf3r',
        'nailgun_bug': 'ab_t4kkyw0yaaet',
        'airgun_bug': 'ab_u7umbjyvti7a',
        'system_issue': 'si001',
        'zalenium_issue': 'si_rhufdawx03e8',
        'to_investigate': 'ti001',
        'no_defect': 'nd001',
    }
    statuses = ['FAILED', 'PASSED', 'SKIPPED', 'INTERRUPTED', 'IN_PROGRESS']
    importance_levels = ['Low', 'Medium', 'High', 'Critical', 'Fips']

    def __init__(self, rp_url, rp_api_key, rp_project):
        """Configure the settings and initiate report portal properties"""
        if not settings.configured:
            settings.configure()
        self.rp_url = rp_url
        self.rp_project = rp_project
        self.rp_api_key = rp_api_key
        self.rp_project_settings = None

        # fetch the project settings
        settings_req = requests.get(
            url=f'{self.api_url}/settings', headers=self.headers, verify=False
        )
        settings_req.raise_for_status()
        self.rp_project_settings = settings_req.json()

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

    def get_launches(
        self, sat_version=None, include_unfinished=False, importances=None, name=None, uuid=None
    ):
        """Returns Report Portal launches customized by sat_version, launch_name and
        latest number of launches sorted by latest sat version/snap version.

        This does not include all data of all test items from all launches, but it includes
        just an overview test-item data of every launch in Report Portal

        :param str sat_version: The satellite version
            If its not specified, then latest count of launches of satellite versions returned
        :param bool include_unfinished: Includes launches with status IN_PROGRESS or INTERRUPTED
        :param list importances: A list of importance levels we want to fetch launches for
        :param str name: Name of the launch to be filtered
        :param str uuid: Optional, UUID of the launch to be fetched - overrides the other parameters
        :returns dict: The launches of Report portal.
            if sat_version is given,
            ```{'snap_version1':launch_object1, 'snap_version2':launch_object2}```
            else,
            ```{'sat_version1':{'snap_version1':launch_object1, ..}, 'sat_version2':{}}```
        """
        # fixme: we might want to implement pagination eventually
        if importances is None:
            importances = self.importance_levels
        params = {'page.page': 1, 'page.size': 20, 'page.sort': 'startTime,desc'}
        if uuid is not None:
            params['filter.eq.uuid'] = uuid
        else:
            if name is not None:
                params['filter.eq.name'] = name
            if sat_version is not None:
                # update when https://github.com/reportportal/reportportal/issues/1094 is fixed
                params['filter.has.attributeValue'] = sat_version
                params['filter.any.attributeValue'] = ','.join(importances)
            if not include_unfinished:
                # This should simply apply a JAVA API filter to exclude "IN_PROGRESS"
                # and "INTERRUPTED launches. Useful in cases the launch lifecycle is managed
                # outside of report portal and a current launch has been already started
                params['filter.ne.status'] = "IN_PROGRESS"

        resp = requests.get(
            url=f'{self.api_url}/launch', headers=self.headers, params=params, verify=False
        )
        resp.raise_for_status()
        # this should further filter out unfinished launches as RP API currently doesn't
        # support usage of the same filter type multiple times (filter.ne.status)
        launches = [
            launch for launch in resp.json()['content'] if launch['status'] not in ['INTERRUPTED']
        ]
        return launches

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_fixed(10),
    )
    def get_tests(self, launch=None, **test_args):
        """Returns tests data customized by kwargs parameters.

        This is a main function that will be called to retrieve the tests data
        of a particular test status or/and defect_type

        :param str launch: Dict of a target launch to fetch test items for
        :param dict test_args: apply the given filters and their values to the search request
        :returns dict: All filtered tests dict based on params data keyed by test name and test
            properties as value, in format -
            ```{'test_name1':test1_properties_dict, 'test_name2':test2_properties_dict}```
        """
        params = {
            'page.size': 50,
            'page.sort': 'name',
            'filter.eq.launchId': launch["id"],
            'filter.ne.type': "SUITE",
        }

        # parse the test filter parameters and turn them into API filter parameters
        if test_args is None:
            test_args = {}
        if test_args.get('status'):
            params['filter.in.status'] = ','.join(test_args['status']).upper()
        if test_args.get('defect_types'):
            params['filter.in.issueType'] = ','.join(
                [ReportPortal.defect_types[t] for t in test_args['defect_types']]
            )
        if test_args.get('user'):
            params['filter.has.attributeKey'] = 'assignee'
            params['filter.has.attributeValue'] = test_args['user']

        # send HTTP request to RP API, retrieve the paginated results and join them together
        page = 1
        total_pages = 1
        resp_tests = []
        while page <= total_pages:
            logger.debug(page)
            params['page.page'] = page
            resp = requests.get(
                url=f'{self.api_url}/item',
                headers=self.headers,
                params=params,
                verify=False,
            )
            resp.raise_for_status()
            resp_tests.extend(resp.json()['content'])
            total_pages = resp.json()['page']['totalPages']
            page += 1

        # Only select tests matching the supplied paths. This is a workaround for RP API limitation
        # - unable to combine multiple filters of a same type
        if test_args.get('paths'):
            resp_tests = [
                test
                for test in resp_tests
                if any([path for path in test_args['paths'] if path in test['name']])
            ]
        return resp_tests
