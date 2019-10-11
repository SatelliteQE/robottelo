"""An issue handler must expose the following functions:

# `is_open_<handler_code>(issue, data=None)`

  e.g: is_open_bz, is_open_gh, is_open_jr for Bugzilla, Github and Jira.

  This function is routed from `robottelo.helpers.is_open` that is also used
  to check for in the `pytest.mark.skip_if_open` marker.

  It receives the issue handler code and number ex: `BZ:123456` for Bugzilla.

  It returns a bool, True is issue is open.


# `should_deselect_<handler_code>(issue, data)`

  e.g: should_deselect_bz for Bugzilla.

  This function is routed from `robottelo.helpers.should_deselect` and
  it is used to dinamically mark a test case with `pytest.mark.deselect`

  It receives the issue handler code and number ex: `BZ:123456` for Bugzilla.

  It returns a bool


# collect_data_<handler_code>(collected_data, cached_data)

  e.g: collect_data_bz for Bugzilla

  This function takes a `collected_data` dict and calls <handler> REST API
  to collect information about the issue then it contributes in-place to the
  `collected_data` dict.

  If `cached_data` is passed, it is used instead of calling the API.


# TODO: handlers to be implemented:
github.py: GH:satelliteqe/robottelo#123
gitlab.py: GL:path/to/repo#123
jira.py: JR:SATQE-4561
redmine.py: RM:pulp.plan.io#5580
"""
# pragma: no cover
