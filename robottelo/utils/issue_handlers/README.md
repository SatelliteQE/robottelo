# Issue tracker handlers

Issue handlers are modules exposing functions that collects and calculates statuses for issue trackers such as Bugzilla, Jira and Github.

## Implementation of issue handler

Issue handler should expose 3 functions.

- is_open_{handler} - called from `robottelo.helpers.is_open`
- should_deselect_{handler} - called from `robottelo.helpers.should_deselect`
- collect_data_{handler} - called from `robottelo.helpers.generate_issue_collection`


### `is_open_<handler_code>(issue, data=None)`

e.g: `is_open_jira` for Jira.

It receives the issue id as string ex: `SAT-123456` for Jira.

It returns a bool, `True` is issue is open.

### `should_deselect_<handler_code>(issue, data)`

e.g: `should_deselect_jira` for Jira.

This function is dispatched from `robottelo.helpers.should_deselect` and
it is used on `conftest.py` to dynamically mark a test case with `pytest.mark.deselect`

It receives the issue id as string ex: `SAT-123456` for Jira.

It returns a bool, `True` if test should be deselected.

### collect_data_<handler_code>(collected_data, cached_data)

e.g: `collect_data_jira` for Jira.

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
            },
            ...
        ]
    },
    ...
}
```
---

## Issue handlers implemented

- `.jira.py`: SAT-22761

## Issue handlers to be implemented

- `.github.py`: GH:satelliteqe/robottelo#123
- `.gitlab.py`: GL:path/to/repo#123

## Issue handlers removed

- `.bugzilla.py`: BZ:12345