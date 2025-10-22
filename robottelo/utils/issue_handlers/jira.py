from collections import defaultdict
import json
from pathlib import Path
import re
import time

import pytest
import requests
from wait_for import TimedOutError, wait_for

from robottelo.config import settings
from robottelo.constants import (
    JIRA_CLOSED_STATUSES,
    JIRA_ONQA_STATUS,
    JIRA_OPEN_STATUSES,
    JIRA_WONTFIX_RESOLUTIONS,
)
from robottelo.logging import logger

# match any version as in `sat-6.14.x` or `sat-6.13.0` or `6.13.9`
# The .version group being a `d.d` string that can be casted to Version()
VERSION_RE = re.compile(r'(?:sat-)*?(?P<version>\d\.\d)\.\w*')

common_jira_fields = ['key', 'summary', 'status', 'labels', 'resolution', 'fixVersions']

mapped_response_fields = {
    'key': "{obj_name}['key']",
    'summary': "{obj_name}['fields']['summary']",
    'status': "{obj_name}['fields']['status']['name']",
    'labels': "{obj_name}['fields']['labels']",
    'resolution': "{obj_name}['fields']['resolution']['name'] if {obj_name}['fields']['resolution'] else ''",
    'fixVersions': "[ver['name'] for ver in {obj_name}['fields']['fixVersions']] if {obj_name}['fields']['fixVersions'] else []",
    # Custom Field - SFDC Cases Counter
    'customfield_12313440': "{obj_name}['fields']['customfield_12313440']",
}


class JiraStatusCache:
    """Handles caching of Jira issue statuses to reduce API calls.
    This class manages a local cache of Jira issue data, allowing for
    efficient retrieval and storage of issue statuses. The cache is
    periodically cleaned to remove expired entries based on a configurable
    time-to-live (TTL) value.
    """

    def __init__(self):
        self.cache_file = Path(settings.jira.cache_file)
        self.cache_ttl_days = settings.jira.cache_ttl_days
        self.cache = self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            logger.debug(f"Loading Jira cache from {self.cache_file}")
            data = json.loads(self.cache_file.read_text())
            self._clean_expired_entries(data)
            cache = data.get("issues", {})
            logger.debug(f"Loaded {len(cache)} entries from Jira cache")
            return cache
        logger.debug("Jira cache file does not exist, using empty cache")
        return {}

    def get(self, issue_id):
        return self.cache.get(issue_id)

    def get_many(self, issue_ids):
        results = {issue_id: self.cache.get(issue_id) for issue_id in issue_ids}
        logger.debug(
            f"Retrieved {sum(1 for v in results.values() if v is not None)} entries from cache"
        )
        return results

    def update(self, issue_id, data):
        self.cache[issue_id] = {"data": data, "timestamp": time.time()}

    def update_many(self, issues_data):
        for issue_id, data in issues_data.items():
            self.update(issue_id, data)

    def save(self):
        logger.debug(f"Saving {len(self.cache)} entries to Jira cache file")
        self.cache_file.write_text(json.dumps({"issues": self.cache}))

    def _clean_expired_entries(self, data):
        now = time.time()
        ttl = self.cache_ttl_days * 86400
        old_count = len(data.get("issues", {}))
        self.cache = {
            key: value
            for key, value in data.get("issues", {}).items()
            if now - value.get("timestamp", 0) <= ttl
        }
        logger.debug(f"Cleaned expired cache entries: {old_count} → {len(self.cache)}")


# Create a global instance of JiraStatusCache
jira_cache = JiraStatusCache()


def sanitized_issue_data(issue, out_fields):
    """fetches the value for all the given fields from a given jira issue

    :param issue: The json data for a jira issue
    :type issue: dict
    :param out_fields: The fields to return from the jira issue
    :type out_fields: list
    """
    return {
        field: eval(mapped_response_fields[field].format(obj_name=issue)) for field in out_fields
    }


def is_open_jira(issue_id, data=None):
    """Check if specific Jira is open consulting a cached `data` dict or calling Jira REST API.

    :param issue_id: The Jira reference e.g: SAT-20548
    :type issue_id: str
    :param data: Issue data indexed by issue id or None
    :type data: dict
    """
    issue_id = issue_id.strip()
    jira = try_from_cache(issue_id, data)
    if jira.get("is_open") is not None:  # issue has been already processed
        return jira["is_open"]

    jira = follow_duplicates(jira)
    status = jira.get('status', '')
    resolution = jira.get('resolution', '')
    logger.debug(f"{issue_id} Jira status is '{status}' and resolution is '{resolution}'")
    # Jira is explicitly in OPEN status
    if status in JIRA_OPEN_STATUSES:
        return True

    # Jira is Closed with a resolution in (Done, Done-Errata, ...)
    return status not in JIRA_CLOSED_STATUSES and status != JIRA_ONQA_STATUS


def are_all_jira_open(issue_ids, data=None):
    """Check if all Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    :param issue_ids: The Jira reference e.g: ['SAT-20548', 'SAT-20548']
    :type issue_ids: list
    :param data: Issue data indexed by issue id or None
    :type data: dict
    """
    return all(is_open_jira(issue_id, data) for issue_id in issue_ids)


def are_any_jira_open(issue_ids, data=None):
    """Check if any of the Jira is open consulting a cached `data` dict or
    calling Jira REST API.

    :param issue_ids: The Jira reference e.g: ['SAT-20548', 'SAT-20548']
    :type issue_ids: list
    :param data: Issue data indexed by issue id or None
    :type data: dict
    """
    return any(is_open_jira(issue_id, data) for issue_id in issue_ids)


def should_deselect_jira(issue_id, data=None):
    """Check if test should be deselected based on marked issue_id.

    :param issue_id: The Jira reference e.g: SAT-12345
    :type issue_id: str
    :param data: Issue data indexed by issue id or None
    :type data: dict
    """
    issue_id = issue_id.strip()
    jira = try_from_cache(issue_id, data)
    if jira.get("is_deselected") is not None:  # issue has been already processed
        return jira["is_deselected"]

    jira = follow_duplicates(jira)

    return (
        jira.get('status') in JIRA_CLOSED_STATUSES
        and jira.get('resolution') in JIRA_WONTFIX_RESOLUTIONS
    )


def follow_duplicates(jira):
    """recursively load the duplicate data

    :param jira: Jira response from Jira REST API
    """
    if jira.get('dupe_data'):
        jira = follow_duplicates(jira['dupe_data'])
    return jira


def try_from_cache(issue_id, data=None):
    """Try to fetch issue from given data cache or previous loaded on pytest.

    :param issue_id: The Jira reference e.g: SAT-12345
    :type issue_id: str
    :param data: Issue data indexed by issue id or None
    :type data: dict
    """
    try:
        # First try using data parameter
        if data:
            return data

        # Then try from pytest cached data - with safe attribute check
        if (
            hasattr(pytest, 'issue_data')
            and issue_id in getattr(pytest, 'issue_data', {})
            and pytest.issue_data.get(issue_id, {}).get('data')
        ):
            return pytest.issue_data[issue_id]['data']

        # Finally try from JiraStatusCache
        cached_data = jira_cache.get(issue_id)
        if cached_data:
            return cached_data.get('data')

        raise ValueError
    except (KeyError, AttributeError, ValueError):  # pragma: no cover
        # If not then call Jira API again
        return get_single_jira(issue_id)


def collect_data_jira(collected_data, cached_data):  # pragma: no cover
    """Collect data from Jira API and aggregate in a dictionary.

    :param collected_data: dict with Jira issues collected by pytest
    :type collected_data: dict
    :param cached_data: Cached data previously loaded from API
    :type cached_data: dict
    """
    # Load persistent cache if available
    if not cached_data:
        issue_ids = [item for item in collected_data if item.startswith('SAT-')]
        cached_data = {
            issue_id: {'data': data['data']}
            for issue_id, data in jira_cache.get_many(issue_ids).items()
            if data is not None
        }

    jira_data = (
        get_data_jira(
            [item for item in collected_data if item.startswith('SAT-')], cached_data=cached_data
        )
        or []
    )
    for data in jira_data:
        # If Jira is CLOSED/DUPLICATE collect the duplicate
        collect_dupes(data, collected_data, cached_data=cached_data)

        jira_key = data['key']
        data["is_open"] = is_open_jira(jira_key, data)
        collected_data[jira_key]['data'] = data


def collect_dupes(jira, collected_data, cached_data=None):  # pragma: no cover
    """Recursively find for duplicates

    :param jira: Jira response from Jira REST API
    :type jira: dict
    :param collected_data: dict with Jira issues collected by pytest
    :type collected_data: dict
    :param cached_data: Cached data previously loaded from API
    :type cached_data: dict
    """
    cached_data = cached_data or {}
    if jira.get('resolution') == 'Duplicate':
        # Collect duplicates
        jira['dupe_data'] = get_single_jira(jira.get('dupe_of'), cached_data=cached_data)
        dupe_key = jira['dupe_of']
        # Store Duplicate also in the main collection for caching
        if dupe_key not in collected_data:
            collected_data[dupe_key]['data'] = jira['dupe_data']
            collected_data[dupe_key]['is_dupe'] = True
            collect_dupes(jira['dupe_data'], collected_data, cached_data)


# --- API Calls ---

# cannot use lru_cache in functions that has unhashable args
CACHED_RESPONSES = defaultdict(dict)


def get_jira(jql, fields=None):
    """Accepts the jql to retrieve the data from Jira for the given fields

    :param jql: The query for retrieving the issue(s) details from jira
    :type jql: str
    :param fields: The custom fields in query to retrieve the data for
    :type fields: list
    :returns: Jira object of response after status check
    :rtype: dict
    """
    params = {"jql": jql}
    if fields:
        params.update({"fields": ",".join(fields)})

    def _make_request():
        try:
            response = requests.get(
                f"{settings.jira.url}/rest/api/latest/search/",
                params=params,
                headers={"Authorization": f"Bearer {settings.jira.api_key}"},
            )
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 429:
                logger.warning("Hit Jira API rate limit (429). Will retry after wait period.")
            raise

    try:
        return wait_for(
            _make_request,
            timeout=80,
            delay=20,
            attempts=4,
            handle_exception=True,
        ).out
    except TimedOutError as err:
        logger.error(f"Maximum retries reached when accessing Jira API: {err}")
        raise


def get_data_jira(issue_ids, cached_data=None, jira_fields=None):  # pragma: no cover
    """Get a list of marked Jira data and query Jira REST API.

    :param issue_ids: Jira issue ids to get data for
    :type issue_ids: list
    :param cached_data: Cached data previously loaded from API
    :type cached_data: dict
    :param jira_fields: List of fields to be retrieved by a jira issue GET request
    :type jira_fields: list
    :returns: List of Jira object of response after status check
    :rtype: list of dict
    """
    if not jira_fields:
        jira_fields = common_jira_fields

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

    # Check JiraStatusCache for all issues
    cached_issues = jira_cache.get_many(issue_ids)
    cached_issues = {k: v for k, v in cached_issues.items() if v is not None}

    remaining_issues = [issue for issue in issue_ids if issue not in cached_issues]

    # If all issues were in cache, return them
    if not remaining_issues:
        logger.debug(f"Using JiraStatusCache for {set(issue_ids)}")
        return [cached_issues[issue_id]['data'] for issue_id in issue_ids]

    # Ensure API key is set
    if not settings.jira.api_key:
        logger.warning("Config file is missing jira api_key. Provide api_key or a jira_cache.json.")
        # Provide default data for collected Jira's.
        default_data = [get_default_jira(issue_id) for issue_id in remaining_issues]
        # Update cache with defaults
        for issue in default_data:
            jira_cache.update(issue['key'], issue)
        jira_cache.save()

        # Return combination of cached and default data
        return [
            cached_issues[issue_id]['data'] for issue_id in issue_ids if issue_id in cached_issues
        ] + default_data

    # No cached data so Call Jira API for remaining issues
    logger.debug(f"Calling Jira API for {set(remaining_issues)}")
    # Following fields are dynamically calculated/loaded
    for field in ('is_open', 'version'):
        assert field not in jira_fields

    # Generate jql
    if isinstance(remaining_issues, str):
        remaining_issues = [issue_id.strip() for issue_id in remaining_issues.split(',')]
    jql = ' OR '.join([f"id = {issue_id}" for issue_id in remaining_issues])
    response = get_jira(jql, jira_fields)
    data = response.json().get('issues')
    # Clean the data, only keep the required info.
    fetched_data = [sanitized_issue_data(issue, jira_fields) for issue in data if issue is not None]

    # Update cache with new data
    for issue in fetched_data:
        jira_cache.update(issue['key'], issue)
    jira_cache.save()

    # Combine cached and fetched data
    result_data = [
        cached_issues[issue_id]['data'] for issue_id in issue_ids if issue_id in cached_issues
    ] + fetched_data
    CACHED_RESPONSES['get_data'][str(sorted(issue_ids))] = result_data
    return result_data


def get_single_jira(issue_id, cached_data=None):  # pragma: no cover
    """Call Jira API to get a single Jira data and cache it

    :param issue_id: Jira issue id
    :type issue_id: str
    :param cached_data: Cached data previously loaded from API
    :type cached_data: dict
    """
    issue_id = issue_id.strip()
    cached_data = cached_data or {}
    jira_data = CACHED_RESPONSES['get_single'].get(issue_id)
    if not jira_data:
        try:
            # First try from provided cache
            if issue_id in cached_data:
                jira_data = cached_data[issue_id]['data']
            else:
                # Then try from JiraStatusCache
                cached = jira_cache.get(issue_id)
                if cached:
                    jira_data = cached.get('data')
                else:
                    # Finally call API
                    try:
                        jira_data = get_data_jira([issue_id], cached_data)
                        jira_data = jira_data and jira_data[0]
                    except TimedOutError:
                        logger.warning(
                            f"Failed to fetch data for {issue_id} after retries. Using default."
                        )
                        jira_data = get_default_jira(issue_id)

                    # Update cache with new data if found
                    if jira_data:
                        jira_cache.update(issue_id, jira_data)
                        jira_cache.save()
        except (KeyError, TypeError):
            # Return default if anything goes wrong
            jira_data = get_default_jira(issue_id)

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
    labels=None,
):
    """Adds a new comment to a Jira issue.

    :param issue_id: Jira issue id, ex. SAT-12232
    :type issue_id: str
    :param comment: Comment to add on the issue.
    :type comment: str
    :param comment_type: Type of comment to add.
    :type comment_type: str
    :param comment_visibility: Comment visibility
    :type comment_visibility: str
    :param labels: Add/Remove Jira labels, ex. [{'add':'tests_passed'},{'remove':'tests_failed'}]
    :type labels: list
    :returns: Response from Jira API
    :rtype: list of dicts
    """
    issue_id = issue_id.strip()
    # Raise a warning if any of the following option is not set. Note: It's a xor condition.
    if settings.jira.enable_comment != bool(pytest.jira_comments):
        logger.warning(
            'Jira comments are currently disabled for this run. '
            'To enable it, please set "enable_comment" to "true" in "config/jira.yaml '
            'and provide --jira-comment pytest option."'
        )
        return None
    if labels:
        logger.debug(f"Updating labels for {issue_id} issue. \n labels: \n {labels}")
        response = requests.put(
            f"{settings.jira.url}/rest/api/latest/issue/{issue_id}/",
            json={"update": {"labels": labels}},
            headers={"Authorization": f"Bearer {settings.jira.api_key}"},
        )
        response.raise_for_status()
    logger.debug(f"Adding a new comment on {issue_id} Jira issue. \n comment: \n {comment}")
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
