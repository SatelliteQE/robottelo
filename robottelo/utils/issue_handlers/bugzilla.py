import re
from collections import defaultdict

import pytest
import requests
from packaging.version import Version
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from robottelo.config import settings
from robottelo.constants import CLOSED_STATUSES
from robottelo.constants import OPEN_STATUSES
from robottelo.constants import WONTFIX_RESOLUTIONS
from robottelo.host_info import get_sat_version
from robottelo.logging import logger


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

    bz = follow_duplicates(bz)

    # BZ is explicitly in OPEN status
    if bz.get('status') in OPEN_STATUSES:
        return True

    # BZ is CLOSED/WONTFIX so considered not fixed yet, BZ is open
    if bz.get('status') in CLOSED_STATUSES and bz.get('resolution') in WONTFIX_RESOLUTIONS:
        return True

    # BZ is CLOSED with a resolution in (ERRATA, CURRENT_RELEASE, ...)
    # server.version is higher or equal than BZ version
    # Consider fixed,  BZ is not open
    return get_sat_version() < extract_min_version(bz)


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

    bz = follow_duplicates(bz)

    return bz.get('status') in CLOSED_STATUSES and bz.get('resolution') in WONTFIX_RESOLUTIONS


def follow_duplicates(bz):
    """Recursivelly load the duplicate data"""
    if bz.get('dupe_data'):
        bz = follow_duplicates(bz['dupe_data'])
    return bz


def extract_min_version(bz):
    """return target_milestone or min(versions flags) or 0"""
    if bz.get('version') is None:
        tmversion = VERSION_RE.search(bz.get('target_milestone', ''))
        if tmversion:
            bz['version'] = Version(tmversion.group('version'))
        else:
            flag_versions = [
                VERSION_RE.search(flag['name'])
                for flag in bz.get('flags', {})
                if flag['status'] == '+'
            ]
            versions = [
                Version(flag_version.group('version'))
                for flag_version in flag_versions
                if flag_version is not None
            ]
            if versions:
                bz['version'] = min(versions)
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
    except (KeyError, AttributeError):  # pragma: no cover
        # If not then call BZ API again
        return get_single_bz(str(issue).partition(':')[-1])


def collect_data_bz(collected_data, cached_data):  # pragma: no cover
    """Collect data from BUgzilla API and aggregate in a dictionary.

    Arguments:
        collected_data {dict} -- dict with BZs collected by pytest
        cached_data {dict} -- Cached data previous loaded from API
    """
    bz_data = (
        get_data_bz(
            [item.partition(':')[-1] for item in collected_data if item.startswith('BZ:')],
            cached_data=cached_data,
        )
        or []
    )
    for data in bz_data:
        # If BZ is CLOSED/DUPLICATE collect the duplicate
        collect_dupes(data, collected_data, cached_data=cached_data)

        # Collect clones to feed the nagger script for notifications
        collect_clones(data, collected_data, cached_data=cached_data)

        bz_key = f"BZ:{data['id']}"
        data["is_open"] = is_open_bz(bz_key, data)
        collected_data[bz_key]['data'] = data


def collect_dupes(bz, collected_data, cached_data=None):  # pragma: no cover
    """Recursivelly find for duplicates"""
    cached_data = cached_data or {}
    if bz.get('resolution') == 'DUPLICATE':
        # Collect duplicates
        bz['dupe_data'] = get_single_bz(bz.get('dupe_of'), cached_data=cached_data)
        dupe_key = f"BZ:{bz['dupe_of']}"
        # Store Duplicate also in the main collection for caching
        if dupe_key not in collected_data:
            collected_data[dupe_key]['data'] = bz['dupe_data']
            collected_data[dupe_key]['is_dupe'] = True
            collect_dupes(bz['dupe_data'], collected_data, cached_data)


def collect_clones(bz, collected_data, cached_data=None):  # pragma: no cover
    """Recursivelly find for clones.
    This handler does not process clones as part of skipping logic.
    but the data is fetched here to feed nagger script later.
    """
    cached_data = cached_data or {}
    clones = bz.get('clone_ids')
    if bz.get('cf_clone_of'):
        clones.append(bz['cf_clone_of'])

    if clones:
        bz['clones'] = get_data_bz(
            [str(clone_num) for clone_num in clones], cached_data=cached_data
        )
        for clone_data in bz['clones']:
            # Store Clones also in the main collection for caching
            clone_key = f'BZ:{clone_data["id"]}'
            if clone_key not in collected_data:
                collected_data[clone_key]['data'] = clone_data
                collected_data[clone_key]['is_clone'] = True
                collect_clones(clone_data, collected_data, cached_data)


# --- API Calls ---

# cannot use lru_cache in functions that has unhashable args
CACHED_RESPONSES = defaultdict(dict)


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
    if not bz_numbers:
        return []

    cached_by_call = CACHED_RESPONSES['get_data'].get(str(sorted(bz_numbers)))
    if cached_by_call:
        return cached_by_call

    if cached_data:
        logger.debug(f"Using cached data for {set(bz_numbers)}")
        if not all([f'BZ:{number}' in cached_data for number in bz_numbers]):
            logger.debug("There are BZs out of cache.")
        return [item['data'] for _, item in cached_data.items() if 'data' in item]

    # Ensure API key is set
    if not settings.bugzilla.api_key:
        logger.warning(
            "Config file is missing bugzilla api_key "
            "so all tests with skip_if_open mark is skipped. "
            "Provide api_key or a bz_cache.json."
        )
        # Provide default data for collected BZs
        return [get_default_bz(number) for number in bz_numbers]

    # No cached data so Call Bugzilla API
    logger.debug(f"Calling Bugzilla API for {set(bz_numbers)}")
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

    response = requests.get(
        f"{settings.bugzilla.url}/rest/bug",
        params={
            "id": ",".join(set(bz_numbers)),
            "include_fields": ",".join(bz_fields),
        },
        headers={"Authorization": f"Bearer {settings.bugzilla.api_key}"},
    )
    response.raise_for_status()
    data = response.json().get('bugs')
    CACHED_RESPONSES['get_data'][str(sorted(bz_numbers))] = data
    return data


def get_single_bz(number, cached_data=None):  # pragma: no cover
    """Call BZ API to get a single BZ data and cache it"""
    cached_data = cached_data or {}
    bz_data = CACHED_RESPONSES['get_single'].get(number)
    if not bz_data:
        try:
            bz_data = cached_data[f"BZ:{number}"]['data']
        except (KeyError, TypeError):
            bz_data = get_data_bz([str(number)], cached_data)
            bz_data = bz_data and bz_data[0]
        CACHED_RESPONSES['get_single'][number] = bz_data
    return bz_data or get_default_bz(number)


def get_default_bz(number):  # pragma: no cover
    """This is the default BZ data when it is not possible to reach BZ api"""
    return {
        "id": number,
        "is_open": True,  # All marked is skipped
        "is_deselected": False,  # nothing is deselected
        "status": "",
        "resolution": "",
        "clone_ids": [],
        "cf_clone_of": "",
        "error": "missing bugzilla api_key",
    }
