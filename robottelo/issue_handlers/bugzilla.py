import re
import logging

import requests
import pytest

from packaging.version import Version
from tenacity import retry, stop_after_attempt, wait_fixed

from robottelo.config import settings
from robottelo.config.base import ImproperlyConfigured
from robottelo.constants import (
    CLOSED_STATUSES,
    OPEN_STATUSES,
    WONTFIX_RESOLUTIONS
)

LOGGER = logging.getLogger(__name__)

# match any version as in `sat-6.2.x` or `sat-6.2.0` or `6.2.9`
# The .version group being a `d.d` string that can be casted to Version()
VERSION_RE = re.compile(r'(?:sat-)*?(?P<version>\d\.\d)\.\w*')


def is_open_bz(issue, data=None):
    """Check if specific BZ is open consulting a cached `data` dict or
    calling Bugzilla REST API.

    Arguments:
        issue {str} -- The BZ reference e.g: BZ:123456
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    bz = try_from_cache(issue, data)
    if bz.get("is_open") is not None:  # bug has been already processed
        return bz["is_open"]
    bz = follow_dupes_and_clones(bz)

    # BZ is explicitly in OPEN status
    if bz['status'] in OPEN_STATUSES:
        return True

    # BZ is CLOSED/WONTFIX so considered not fixed yet, BZ is open
    if (
        bz['status'] in CLOSED_STATUSES
        and bz['resolution'] in WONTFIX_RESOLUTIONS
    ):
        return True

    # BZ is CLOSED with a resolution in (ERRATA, CURRENT_RELEASE, ...)
    # server.version is higher or equal than BZ version
    # Consider fixed,  BZ is not open
    if settings.server.version >= extract_min_version(bz):
        return False

    # Not in OPEN_STATUSES
    # Not in Wontfix resolution
    # server.version is lower than BZ min version
    # fixed in next version, not backported
    # so BZ is open
    return True


def should_deselect_bz(issue, data=None):
    """Check if test should be deselected based on marked issue.

    1. Resolution WONTFIX/CANTFIX/DEFERRED should deselect

    Arguments:
        issue {str} -- The BZ reference e.g: BZ:123456
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    bz = try_from_cache(issue, data)
    if bz.get("is_deselected") is not None:  # bug has been already processed
        return bz["is_deselected"]
    bz = follow_dupes_and_clones(bz)

    return (
        bz['status'] in CLOSED_STATUSES
        and bz['resolution'] in WONTFIX_RESOLUTIONS
    )


def follow_dupes_and_clones(bz):
    """Check if BZ has duplicates and clones.

    If has a dupe, consider dupe in place of BZ.
    If has clones, consider the clone with the minimum version.

    Arguments:
        bz {dict} -- A dict containing bz data.
    """
    if bz.get('dupe_data'):
        bz = bz['dupe_data']

    max_version = max(settings.server.version, extract_min_version(bz))
    for clone in bz.get('clones', []):
        clone_version = extract_min_version(clone)
        if max_version >= clone_version:
            max_version = clone_version
            bz = clone

    return bz


def extract_min_version(bz):
    """return target_milestone or min(versions flags) or 0"""
    if bz.get('version') is None:
        tmversion = VERSION_RE.search(bz['target_milestone'])
        if tmversion:
            bz["version"] = Version(tmversion.group('version'))
        else:
            flag_versions = [
                VERSION_RE.search(flag['name'])
                for flag in bz['flags']
                if flag['status'] == '+'
            ]
            versions = [
                Version(flag_version.group('version'))
                for flag_version in flag_versions
                if flag_version is not None
            ]
            if versions:
                bz["version"] = min(versions)
    return bz.get('version') or Version('0')  # to allow comparisons


def try_from_cache(issue, data=None):
    """Try to fetch issue from given data cache or previous loaded on pytest.

   Arguments:
        issue {str} -- The BZ reference e.g: BZ:123456
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    try:
        # issue must be passed in `data` argument or already fetched in pytest
        return data or pytest.issue_data[issue]['data']
    except KeyError:  # pragma: no cover
        # If not then call BZ API again
        return get_single_bz(str(issue).partition(':')[-1])


def collect_data_bz(collected_data, cached_data):  # pragma: no cover
    """Collect data from BUgzilla API and aggregate in a dictionary.

    Arguments:
        collected_data {dict} -- dict with BZs collected by pytest
        cached_data {dict} -- Cached data previous loaded from API
    """
    bz_data = get_data_bz(
        [
            item.partition(':')[-1]
            for item in collected_data
            if item.startswith('BZ:')
        ],
        cached_data=cached_data
    )
    for data in bz_data:
        clones = data['clone_ids']
        if data['cf_clone_of']:
            clones.append(data['cf_clone_of'])

        if data["resolution"] == "DUPLICATE":
            # Collect duplicates
            data["dupe_data"] = get_single_bz(
                data["dupe_of"],
                cached_data=cached_data
            )
            # Store Duplicate also in the main collection for caching
            dupe_key = "BZ:{}".format(data["dupe_of"])
            if dupe_key not in collected_data:
                collected_data[dupe_key]['data'] = data["dupe_data"]
        elif clones:
            # Collect clones
            data["clones"] = get_data_bz(
                [str(clone_num) for clone_num in clones],
                cached_data=cached_data
            )
            for clone_data in data["clones"]:
                # Store Clones also in the main collection for caching
                clone_key = "BZ:{}".format(clone_data['id'])
                if clone_key not in collected_data:
                    collected_data[clone_key]['data'] = clone_data

        bz_key = 'BZ:{}'.format(data['id'])
        data["is_open"] = is_open_bz(bz_key, data)
        collected_data[bz_key]['data'] = data


# --- API Calls ---

@retry(
    stop=stop_after_attempt(4),  # Retry 3 times before raising
    wait=wait_fixed(20),  # Wait seconds between retries
)
def get_data_bz(bz_numbers, cached_data=None):  # pragma: no cover
    """Get a list of marked BZ data and query Bugzilla REST API.

    Arguments:
        bz_numbers {list of str} -- ['123456', ...]
        cached_data

    Returns:
        [list of dicts] -- [{'id':..., 'status':..., 'resolution': ...}]
    """
    if cached_data:
        LOGGER.debug("Using cached data for {}".format(set(bz_numbers)))
        if not all(
            ['BZ:{}'.format(number) in cached_data for number in bz_numbers]
        ):
            LOGGER.debug("There are BZs out of cache.")
        return [
            item['data']
            for _, item in cached_data.items()
            if 'data' in item
        ]

    # No cached data so Call Bugzilla API
    LOGGER.debug("Calling Bugzilla API for {}".format(set(bz_numbers)))
    bz_fields = [
        "id",
        "summary",
        "status",
        "resolution",
        "cf_last_closed",
        "last_change_time",
        "creation_time",
        "flags",
        "keywords",
        "dupe_of",
        "target_milestone",
        "cf_clone_of",
        "clone_ids",
        "depends_on",
    ]
    # Following fields are dynamically calculated/loaded
    for field in ('is_open', 'clones', 'version'):
        assert field not in bz_fields

    # Ensure API key is set
    if not settings.bugzilla.api_key:
        raise ImproperlyConfigured("Config file is missing bugzilla api_key")

    response = requests.get(
        "{}/rest/bug".format(settings.bugzilla.url),
        params={
            "id": ",".join(set(bz_numbers)),
            "api_key": settings.bugzilla.api_key,
            "include_fields": ",".join(bz_fields),
        },
    )
    response.raise_for_status()
    return response.json()["bugs"]


def get_single_bz(number, cached_data=None):  # pragma: no cover
    """Call BZ API to get a single BZ data and cache it"""
    bz_data = get_data_bz([str(number)], cached_data)
    return bz_data[0] if bz_data else {}
