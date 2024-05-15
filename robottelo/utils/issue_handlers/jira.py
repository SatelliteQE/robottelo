from collections import defaultdict
import re

from packaging.version import Version
import pytest
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from robottelo.config import settings
from robottelo.constants import (
    JIRA_CLOSED_STATUSES,
    JIRA_ONQA_STATUS,
    JIRA_OPEN_STATUSES,
    JIRA_WONTFIX_RESOLUTIONS,
)
from robottelo.hosts import get_sat_version
from robottelo.logging import logger

# match any version as in `sat-6.14.x` or `sat-6.13.0` or `6.13.9`
# The .version group being a `d.d` string that can be casted to Version()
VERSION_RE = re.compile(r'(?:sat-)*?(?P<version>\d\.\d)\.\w*')


def is_open_jira(issue, data=None):
    """Check if specific Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    Arguments:
        issue {str} -- The Jira reference e.g: SAT-20548
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    jira = try_from_cache(issue, data)
    if jira.get("is_open") is not None:  # issue has been already processed
        return jira["is_open"]

    jira = follow_duplicates(jira)
    status = jira.get('status', '')
    resolution = jira.get('resolution', '')

    # Jira is explicitly in OPEN status
    if status in JIRA_OPEN_STATUSES:
        return True

    # Jira is Closed/Obsolete so considered not fixed yet, Jira is open
    if status in JIRA_CLOSED_STATUSES and resolution in JIRA_WONTFIX_RESOLUTIONS:
        return True

    # Jira is Closed with a resolution in (Done, Done-Errata, ...)
    # server.version is higher or equal than Jira fixVersion
    # Consider fixed, Jira is not open
    fix_version = jira.get('fixVersions')
    if fix_version:
        return get_sat_version() < Version(min(fix_version))
    return status not in JIRA_CLOSED_STATUSES and status != JIRA_ONQA_STATUS


def are_all_jira_open(issues, data=None):
    """Check if all Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    Arguments:
        issues {list} -- The Jira reference e.g: ['SAT-20548', 'SAT-20548']
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    return all(is_open_jira(issue, data) for issue in issues)


def are_any_jira_open(issues, data=None):
    """Check if any of the Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    Arguments:
        issues {list} -- The Jira reference e.g: ['SAT-20548', 'SAT-20548']
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    return any(is_open_jira(issue, data) for issue in issues)


def should_deselect_jira(issue, data=None):
    """Check if test should be deselected based on marked issue.

    1. Resolution "Obsolete" should deselect

    Arguments:
        issue {str} -- The Jira reference e.g: SAT-12345
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """

    jira = try_from_cache(issue, data)
    if jira.get("is_deselected") is not None:  # issue has been already processed
        return jira["is_deselected"]

    jira = follow_duplicates(jira)

    return (
        jira.get('status') in JIRA_CLOSED_STATUSES
        and jira.get('resolution') in JIRA_WONTFIX_RESOLUTIONS
    )


def follow_duplicates(jira):
    """recursively load the duplicate data"""
    if jira.get('dupe_data'):
        jira = follow_duplicates(jira['dupe_data'])
    return jira


def try_from_cache(issue, data=None):
    """Try to fetch issue from given data cache or previous loaded on pytest.

    Arguments:
         issue {str} -- The Jira reference e.g: SAT-12345
         data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    try:
        # issue must be passed in `data` argument or already fetched in pytest
        if not data and not len(pytest.issue_data[issue]['data']):
            raise ValueError
        return data or pytest.issue_data[issue]['data']
    except (KeyError, AttributeError, ValueError):  # pragma: no cover
        # If not then call Jira API again
        return get_single_jira(str(issue))


def collect_data_jira(collected_data, cached_data):  # pragma: no cover
    """Collect data from Jira API and aggregate in a dictionary.

    Arguments:
        collected_data {dict} -- dict with Jira issues collected by pytest
        cached_data {dict} -- Cached data previous loaded from API
    """
    jira_data = (
        get_data_jira(
            [item for item in collected_data if item.startswith('SAT-')],
            cached_data=cached_data,
        )
        or []
    )
    for data in jira_data:
        # If Jira is CLOSED/DUPLICATE collect the duplicate
        collect_dupes(data, collected_data, cached_data=cached_data)

        jira_key = f"{data['key']}"
        data["is_open"] = is_open_jira(jira_key, data)
        collected_data[jira_key]['data'] = data


def collect_dupes(jira, collected_data, cached_data=None):  # pragma: no cover
    """Recursively find for duplicates"""
    cached_data = cached_data or {}
    if jira.get('resolution') == 'Duplicate':
        # Collect duplicates
        jira['dupe_data'] = get_single_jira(jira.get('dupe_of'), cached_data=cached_data)
        dupe_key = f"{jira['dupe_of']}"
        # Store Duplicate also in the main collection for caching
        if dupe_key not in collected_data:
            collected_data[dupe_key]['data'] = jira['dupe_data']
            collected_data[dupe_key]['is_dupe'] = True
            collect_dupes(jira['dupe_data'], collected_data, cached_data)


# --- API Calls ---

# cannot use lru_cache in functions that has unhashable args
CACHED_RESPONSES = defaultdict(dict)


@retry(
    stop=stop_after_attempt(4),  # Retry 3 times before raising
    wait=wait_fixed(20),  # Wait seconds between retries
)
def get_data_jira(jira_numbers, cached_data=None):  # pragma: no cover
    """Get a list of marked Jira data and query Jira REST API.

    Arguments:
        jira_numbers {list of str} -- ['SAT-12345', ...]
        cached_data {dict} -- Cached data previous loaded from API

    Returns:
        [list of dicts] -- [{'id':..., 'status':..., 'resolution': ...}]
    """
    if not jira_numbers:
        return []

    cached_by_call = CACHED_RESPONSES['get_data'].get(str(sorted(jira_numbers)))
    if cached_by_call:
        return cached_by_call

    if cached_data:
        logger.debug(f"Using cached data for {set(jira_numbers)}")
        if not all([f'{number}' in cached_data for number in jira_numbers]):
            logger.debug("There are Jira's out of cache.")
        return [item['data'] for _, item in cached_data.items() if 'data' in item]

    # Ensure API key is set
    if not settings.jira.api_key:
        logger.warning(
            "Config file is missing jira api_key "
            "so all tests with skip_if_open mark is skipped. "
            "Provide api_key or a jira_cache.json."
        )
        # Provide default data for collected Jira's.
        return [get_default_jira(number) for number in jira_numbers]

    # No cached data so Call Jira API
    logger.debug(f"Calling Jira API for {set(jira_numbers)}")
    jira_fields = [
        "key",
        "summary",
        "status",
        "resolution",
        "fixVersions",
    ]
    # Following fields are dynamically calculated/loaded
    for field in ('is_open', 'version'):
        assert field not in jira_fields

    # Generate jql
    jql = ' OR '.join([f"id = {id}" for id in jira_numbers])

    response = requests.get(
        f"{settings.jira.url}/rest/api/latest/search/",
        params={
            "jql": jql,
            "fields": ",".join(jira_fields),
        },
        headers={"Authorization": f"Bearer {settings.jira.api_key}"},
    )
    response.raise_for_status()
    data = response.json().get('issues')
    # Clean the data, only keep the required info.
    data = [
        {
            'key': issue['key'],
            'summary': issue['fields']['summary'],
            'status': issue['fields']['status']['name'],
            'resolution': issue['fields']['resolution']['name']
            if issue['fields']['resolution']
            else '',
            'fixVersions': [ver['name'] for ver in issue['fields']['fixVersions']]
            if issue['fields']['fixVersions']
            else [],
        }
        for issue in data
        if issue is not None
    ]
    CACHED_RESPONSES['get_data'][str(sorted(jira_numbers))] = data
    return data


def get_single_jira(number, cached_data=None):  # pragma: no cover
    """Call Jira API to get a single Jira data and cache it"""
    cached_data = cached_data or {}
    jira_data = CACHED_RESPONSES['get_single'].get(number)
    if not jira_data:
        try:
            jira_data = cached_data[f"{number}"]['data']
        except (KeyError, TypeError):
            jira_data = get_data_jira([str(number)], cached_data)
            jira_data = jira_data and jira_data[0]
        CACHED_RESPONSES['get_single'][number] = jira_data
    return jira_data or get_default_jira(number)


def get_default_jira(number):  # pragma: no cover
    """This is the default Jira data when it is not possible to reach Jira api"""
    return {
        "key": number,
        "is_open": True,
        "is_deselected": False,
        "status": "",
        "resolution": "",
        "error": "missing jira api_key",
    }
