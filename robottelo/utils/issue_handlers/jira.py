from collections import defaultdict
import json
from pathlib import Path
import time

from jira import JIRA
from jira.exceptions import JIRAError
import pytest
from wait_for import TimedOutError, wait_for

from robottelo.config import settings
from robottelo.constants import (
    JIRA_CLOSED_STATUSES,
    JIRA_ONQA_STATUS,
    JIRA_OPEN_STATUSES,
    JIRA_WONTFIX_RESOLUTIONS,
)
from robottelo.logging import logger

common_jira_fields = ['key', 'status', 'labels', 'resolution']

FIELD_EXTRACTORS = {
    "key": lambda issue: issue.key,
    "status": lambda issue: issue.fields.status.name if issue.fields.status else "",
    "labels": lambda issue: list(issue.fields.labels or []),
    "resolution": lambda issue: issue.fields.resolution.name if issue.fields.resolution else "",
}


def _issue_to_flat_dict(issue, out_fields):
    """Build a flat dict from a jira Issue object using attribute access."""
    result = {}
    for field in out_fields:
        if field in FIELD_EXTRACTORS:
            result[field] = FIELD_EXTRACTORS[field](issue)
        else:
            result[field] = getattr(issue.fields, field, None)
    return result


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
            logger.debug(f"Loaded {len(self.cache)} entries from Jira cache")
            return self.cache
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
        self.cache[issue_id] = data | {"timestamp": time.time()}

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


def is_open_jira(issue_id):
    """Check if specific Jira is open (uses pytest.issue_data, jira_cache, or API).

    :param issue_id: The Jira reference e.g: SAT-20548
    :type issue_id: str
    """
    issue_id = issue_id.strip()
    jira = try_from_cache(issue_id)
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


def are_all_jira_open(issue_ids):
    """Check if all given Jira issues are open."""
    return all(is_open_jira(issue_id) for issue_id in issue_ids)


def are_any_jira_open(issue_ids):
    """Check if any of the given Jira issues is open."""
    return any(is_open_jira(issue_id) for issue_id in issue_ids)


def should_deselect_jira(issue_id):
    """Check if test should be deselected based on marked issue_id."""
    issue_id = issue_id.strip()
    jira = try_from_cache(issue_id)
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


def try_from_cache(issue_id):
    """Fetch issue from pytest.issue_data, jira_cache, or API."""
    try:
        issue = (
            getattr(pytest, 'issue_data', {}).get(issue_id)
            if hasattr(pytest, 'issue_data')
            else None
        )
        if issue and (issue.get('key') or issue.get('status') is not None):
            return issue

        # Finally try from JiraStatusCache
        cached_data = jira_cache.get(issue_id)
        if cached_data:
            return cached_data

        raise ValueError
    except (KeyError, AttributeError, ValueError):  # pragma: no cover
        # If not then call Jira API again
        return get_single_jira(issue_id)


# --- API Calls ---

# cannot use lru_cache in functions that has unhashable args
CACHED_RESPONSES = defaultdict(dict)


def _jira_client():
    """Create a JIRA client with basic auth (email and api_key)."""
    return JIRA(
        server=settings.jira.url,
        basic_auth=(settings.jira.email, settings.jira.api_key),
    )


def get_jira(jql, fields=None):
    """Accepts the jql to retrieve the data from Jira for the given fields

    :param jql: The query for retrieving the issue(s) details from jira
    :type jql: str
    :param fields: The custom fields in query to retrieve the data for
    :type fields: list
    :returns: List of Issue objects from the jira library
    :rtype: list
    """
    fields_str = ','.join(fields) if fields else None

    def _make_request():
        try:
            jira = _jira_client()
            issues = jira.search_issues(jql_str=jql, fields=fields_str)
            return list(issues)
        except JIRAError as err:
            if getattr(err, 'status_code', None) == 429:
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
        return [item for _, item in cached_data.items()]

    # Check JiraStatusCache for all issues
    cached_issues = jira_cache.get_many(issue_ids)
    cached_issues = {k: v for k, v in cached_issues.items() if v is not None}

    remaining_issues = [issue for issue in issue_ids if issue not in cached_issues]

    # If all issues were in cache, return them
    if not remaining_issues:
        logger.debug(f"Using JiraStatusCache for {set(issue_ids)}")
        return [cached_issues[issue_id] for issue_id in issue_ids]

    # Ensure API key is set
    if not (settings.jira.email and settings.jira.api_key):
        logger.warning(
            "Config file is missing either jira email or api_key. Provide Jira email and api_key or a jira_cache.json."
        )
        # Provide default data for collected Jira's.
        default_data = [get_default_jira(issue_id) for issue_id in remaining_issues]
        # Update cache with defaults
        for issue in default_data:
            jira_cache.update(issue['key'], issue)
        jira_cache.save()

        # Return combination of cached and default data
        return [
            cached_issues[issue_id] for issue_id in issue_ids if issue_id in cached_issues
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
    issues = get_jira(jql, jira_fields)
    fetched_data = [
        _issue_to_flat_dict(issue, jira_fields) for issue in issues if issue is not None
    ]

    # Update cache with new data
    for issue in fetched_data:
        jira_cache.update(issue['key'], issue)
    jira_cache.save()

    # Combine cached and fetched data
    result_data = [
        cached_issues[issue_id] for issue_id in issue_ids if issue_id in cached_issues
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
                jira_data = cached_data[issue_id]
            else:
                # Then try from JiraStatusCache
                cached = jira_cache.get(issue_id)
                if cached:
                    jira_data = cached
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
        "error": "missing jira email/api_key",
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
    :returns: Comment response from Jira API
    :rtype: dict
    """
    issue_id = issue_id.strip()
    if settings.jira.enable_comment != bool(getattr(pytest, 'jira_comments', False)):
        logger.warning(
            'Jira comments are currently disabled for this run. '
            'To enable it, please set "enable_comment" to "true" in "config/jira.yaml '
            'and provide --jira-comments pytest option."'
        )
        return None

    jira = _jira_client()

    if labels:
        logger.debug(f"Updating labels for {issue_id} issue. \n labels: \n {labels}")
        issue_url = f"{settings.jira.url}/rest/api/latest/issue/{issue_id}"
        response = jira._session.put(issue_url, json={"update": {"labels": labels}})
        response.raise_for_status()

    logger.debug(f"Adding a new comment on {issue_id} Jira issue. \n comment: \n {comment}")
    url = f"{settings.jira.url}/rest/api/latest/issue/{issue_id}/comment"
    payload = {
        "body": comment,
        "visibility": {
            "type": comment_type,
            "value": comment_visibility,
        },
    }
    response = jira._session.post(url, json=payload)
    response.raise_for_status()
    return response.json()
