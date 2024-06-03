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


def is_open_jira(issue_id, data=None):
    """Check if specific Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    Arguments:
        issue_id {str} -- The Jira reference e.g: SAT-20548
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    jira = try_from_cache(issue_id, data)
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


def are_all_jira_open(issue_ids, data=None):
    """Check if all Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    Arguments:
        issue_ids {list} -- The Jira reference e.g: ['SAT-20548', 'SAT-20548']
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    return all(is_open_jira(issue_id, data) for issue_id in issue_ids)


def are_any_jira_open(issue_ids, data=None):
    """Check if any of the Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    Arguments:
        issue_ids {list} -- The Jira reference e.g: ['SAT-20548', 'SAT-20548']
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    return any(is_open_jira(issue_id, data) for issue_id in issue_ids)


def should_deselect_jira(issue_id, data=None):
    """Check if test should be deselected based on marked issue_id.

    1. Resolution "Obsolete" should deselect

    Arguments:
        issue_id {str} -- The Jira reference e.g: SAT-12345
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """

    jira = try_from_cache(issue_id, data)
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


def try_from_cache(issue_id, data=None):
    """Try to fetch issue from given data cache or previous loaded on pytest.

    Arguments:
         issue_id {str} -- The Jira reference e.g: SAT-12345
         data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    try:
        # issue_id must be passed in `data` argument or already fetched in pytest
        if not data and not len(pytest.issue_data[issue_id]['data']):
            raise ValueError
        return data or pytest.issue_data[issue_id]['data']
    except (KeyError, AttributeError, ValueError):  # pragma: no cover
        # If not then call Jira API again
        return get_single_jira(str(issue_id))


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
def get_data_jira(issue_ids, cached_data=None):  # pragma: no cover
    """Get a list of marked Jira data and query Jira REST API.

    Arguments:
        issue_ids {list of str} -- ['SAT-12345', ...]
        cached_data {dict} -- Cached data previous loaded from API

    Returns:
        [list of dicts] -- [{'id':..., 'status':..., 'resolution': ...}]
    """
    if not issue_ids:
        return []

    cached_by_call = CACHED_RESPONSES['get_data'].get(str(sorted(issue_ids)))
    if cached_by_call:
        return cached_by_call

    if cached_data:
        logger.debug(f"Using cached data for {set(issue_ids)}")
        if not all([f'{number}' in cached_data for number in issue_ids]):
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
        return [get_default_jira(issue_id) for issue_id in issue_ids]

    # No cached data so Call Jira API
    logger.debug(f"Calling Jira API for {set(issue_ids)}")
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
    jql = ' OR '.join([f"id = {issue_id}" for issue_id in issue_ids])

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
    CACHED_RESPONSES['get_data'][str(sorted(issue_ids))] = data
    return data


def get_single_jira(issue_id, cached_data=None):  # pragma: no cover
    """Call Jira API to get a single Jira data and cache it"""
    cached_data = cached_data or {}
    jira_data = CACHED_RESPONSES['get_single'].get(issue_id)
    if not jira_data:
        try:
            jira_data = cached_data[f"{issue_id}"]['data']
        except (KeyError, TypeError):
            jira_data = get_data_jira([str(issue_id)], cached_data)
            jira_data = jira_data and jira_data[0]
        CACHED_RESPONSES['get_single'][issue_id] = jira_data
    return jira_data or get_default_jira(issue_id)


def get_default_jira(issue_id):  # pragma: no cover
    """This is the default Jira data when it is not possible to reach Jira api"""
    return {
        "key": issue_id,
        "is_open": True,
        "is_deselected": False,
        "status": "",
        "resolution": "",
        "error": "missing jira api_key",
    }


def add_comment_on_jira(
    issue_id,
    comment,
    comment_type=settings.jira.comment_type,
    comment_visibility=settings.jira.comment_visibility,
):
    """Adds a new comment to a Jira issue.

    Arguments:
        issue_id {str} -- Jira issue number, ex. SAT-12232
        comment {str}  -- Comment to add on the issue.
        comment_type {str}  -- Type of comment to add.
        comment_visibility {str}  -- Comment visibility.

    Returns:
        [list of dicts] -- [{'id':..., 'status':..., 'resolution': ...}]
    """
    # Raise a warning if any of the following option is not set. Note: It's a xor condition.
    if settings.jira.enable_comment != pytest.jira_comments:
        logger.warning(
            'Jira comments are currently disabled for this run. '
            'To enable it, please set "enable_comment" to "true" in "config/jira.yaml '
            'and provide --jira-comment pytest option."'
        )
        return None
    data = try_from_cache(issue_id)
    if data["status"] in settings.jira.issue_status:
        logger.debug(f"Adding a new comment on {issue_id} Jira issue.")
        response = requests.post(
            f"{settings.jira.url}/rest/api/latest/issue/{issue_id}/comment",
            json={
                "body": comment,
                "visibility": {
                    "type": comment_type,
                    "value": comment_visibility,
                },
            },
            headers={"Authorization": f"Bearer {settings.jira.api_key}"},
        )
        response.raise_for_status()
        return response.json()
    logger.warning(
        f"Jira comments are currently disabled for this issue because it's in {data['status']} state. "
        f"Please update issue_status in jira.conf to overide this behaviour."
    )
    return None
