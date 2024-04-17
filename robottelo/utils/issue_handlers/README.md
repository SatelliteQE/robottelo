# Issue tracker handlers

Issue handlers are modules exposing functions that collects and calculates statuses for issue trackers such as Bugzilla, Jira and Github.

## Implementation of issue handler

Issue handler should expose 3 functions.

- is_open_{handler} - called from `robottelo.helpers.is_open`
- should_deselect_{handler} - called from `robottelo.helpers.should_deselect`
- collect_data_{handler} - called from `robottelo.helpers.generate_issue_collection`


### `is_open_<handler_code>(issue, data=None)`

e.g: `is_open_bz, is_open_gh, is_open_jira` for Bugzilla, Github and Jira.

This function is dispatched from `robottelo.helpers.is_open` that is also used
to check for status in the `pytest.mark.skip_if_open` marker.

It receives the issue handler code and number as a string ex: `BZ:123456` for Bugzilla.

It returns a bool, `True` is issue is open.

### `should_deselect_<handler_code>(issue, data)`

e.g: `should_deselect_bz` for Bugzilla.

This function is dispatched from `robottelo.helpers.should_deselect` and
it is used on `conftest.py` to dynamically mark a test case with `pytest.mark.deselect`

It receives the issue handler code and number as string ex: `BZ:123456` for Bugzilla.

It returns a bool, `True` if test should be deselected.

### collect_data_<handler_code>(collected_data, cached_data)

e.g: `collect_data_bz` for Bugzilla

This function takes a `collected_data` dict and calls the issue tracker API
to collect information about the issue then it contributes in-place to the
`collected_data` dict.

If `cached_data` is passed, it is used instead of calling the API again.

Example of `collected_data`:

```json
{
    "XX:1625783" {
        "data": {
            # data taken from REST api,
            "status": ...,
            "resolution": ...,
            ...
            # Calculated data
            "is_open": bool,
            "is_deselected": bool,
            "clones": [list],
            "dupe_data": {dict}
        },
        "used_in" [
            {
                "filepath": "tests/foreman/ui/test_sync.py",
                "lineno": 124,
                "testcase": "test_positive_sync_custom_ostree_repo",
                "component": "Repositories",
                "usage": "skip_if_open"
            },
            ...
        ]
    },
    ...
}
```
---

## Issue handlers implemented

- `.bugzilla.py`: BZ:123456
- `.jira.py`: SAT-22761

## Issue handlers to be implemented

- `.github.py`: GH:satelliteqe/robottelo#123
- `.gitlab.py`: GL:path/to/repo#123
- `.redmine.py`: RM:pulp.plan.io#5580
