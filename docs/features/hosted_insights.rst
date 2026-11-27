Hosted Insights upload window
=============================

Synthetic uploads to hosted Insights can encounter long ingestion queues during
recurring production upload peaks. Tests marked ``hosted_insights`` are skipped
by default from **23:00 UTC (inclusive) to 10:30 UTC (exclusive)** each day.
The runner's local timezone and daylight-saving time do not affect this policy.

The check runs at the start of each marked test, before pytest sets up that
test's fixtures. It is not evaluated at import or collection time, so a long
suite crossing into the exclusion window skips subsequent marked tests and
xdist workers collect the same tests. Skips include the window and override
instructions in the test report (use ``-rs`` to display reasons).

This controls test start times, not individual upload times: an already-running
test can still upload after the window starts. It does not stop independent
Satellite background uploads or prevent infrastructure that CI provisions
before invoking pytest. It does not automatically defer or reschedule tests.

Marking tests
-------------

Apply the marker to tests whose execution or fixtures upload archives to hosted
Insights or depend on hosted ingestion. This includes fixtures that register
clients even when the test body only checks local report generation. Do not
mark a test merely because it mentions Insights, installs a client package, or
checks a setting. IoP-only tests should remain unmarked. A test that starts with
hosted registration and later enables IoP still needs the marker.

For example::

    @pytest.mark.hosted_insights
    def test_positive_hosted_registration(...):
        ...

For a test covering both hosted and local Insights, mark only the hosted
parameter rather than the whole test::

    @pytest.mark.parametrize(
        'module_target_sat_insights',
        [pytest.param(True, marks=pytest.mark.hosted_insights), False],
        ids=['hosted', 'local'],
        indirect=True,
    )
    def test_positive_registration(module_target_sat_insights, ...):
        ...

Configuration
-------------

Defaults are defined in Robottelo's settings validators and documented in
``conf/rh_cloud.yaml.template``::

    RH_CLOUD:
      SKIP_PEAK_UPLOADS: true
      PEAK_UPLOAD_START_UTC: '23:00'
      PEAK_UPLOAD_END_UTC: '10:30'
      ALLOW_PEAK_UPLOADS: false

Times must be zero-padded ``HH:MM`` strings in UTC; start and end must differ.
Windows that cross midnight and windows within a single day are supported.
Set ``SKIP_PEAK_UPLOADS`` to ``false`` to disable enforcement. The policy only
affects marked tests; it does not replace any other eligibility or skip rules.

Intentional overrides
---------------------

For local or targeted debugging runs::

    pytest tests/foreman/ui/test_registration.py::test_positive_global_registration_end_to_end --allow-hosted-insights-during-peak

Alternatively, use the corresponding Dynaconf environment setting::

    ROBOTTELO_RH_CLOUD__ALLOW_PEAK_UPLOADS=true pytest tests/foreman/ui/test_registration.py::test_positive_global_registration_end_to_end

An override logs a warning when it permits a marked test during the peak. It
bypasses only this time restriction: readiness polling, timeouts, assertions,
and other skip conditions are unchanged.

For PRT, use its existing ``env`` support rather than embedding extra command
arguments in the quoted ``pytest`` value. Post the following as one complete,
single-line comment **without a trailing newline**::

    {trigger: test-robottelo, pytest: 'tests/foreman/ui/test_registration.py::test_positive_global_registration_end_to_end[rhel10-ipv4]', env: {ROBOTTELO_RH_CLOUD__ALLOW_PEAK_UPLOADS: true}}

Scheduling coverage
-------------------

The marker also lets CI select the group explicitly::

    pytest -m hosted_insights
    pytest -m 'not hosted_insights'

Arrange an off-peak CI run during **10:30-23:00 UTC**, with enough time to finish
before the next peak. The guard is not a substitute for scheduling: skipped
tests are not requeued by Robottelo. Jenkins scheduling or PRT deferral requires
a separate CI change. Inspect skip counts so coverage is not silently lost.
