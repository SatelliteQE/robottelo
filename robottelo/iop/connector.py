"""HTTP helpers for Foreman's ``insights_cloud`` Advisor proxy routes.

Foreman's ``foreman_rh_cloud`` plugin exposes Insights Advisor routes (ack,
hostack, rule ack_hosts) behind an ``/insights_cloud`` proxy that forwards to
the hosted Insights API. These routes have no nailgun entity wrapper, so
calls go straight through ``nailgun.client``, the same pattern this repo
already uses elsewhere for non-entity routes (see
``tests/foreman/api/test_activationkey.py``).

The proxy expects:

* an explicit ``organization_id`` query param on every request, since its org
  scoping is normally derived from a browser session
  (``Organization.current``), which a token-authenticated caller never has;
* Foreman's own HTTP basic auth (``robottelo.config.get_credentials()``), not
  a hosted ``x-rh-identity`` header;
* an explicit ``Accept: application/json`` header. Without it, Foreman's
  catch-all router returns a 200 with its HTML app shell instead of
  forwarding to the JSON API, since nothing else in a plain Basic-Auth
  request signals that JSON (not the web UI) is wanted.

*Known issue (being worked on):* mutating calls through this proxy
(``InsightsCloud::UIRequestsController``) currently return a CSRF-related 422
for token-authenticated callers, since that controller inherits Rails'
browser-session CSRF protection rather than Foreman's CSRF-exempt API
controller base. A fix is in progress in ``foreman_rh_cloud``; the tests
built on these helpers assert the correct business behavior and should pass
once it lands. GET-only reads are unaffected.
"""

from urllib.parse import quote

from robottelo.config import get_credentials, get_url

INSIGHTS_CLOUD_PROXY_PATH = '/insights_cloud'
ADVISOR_API_PATH = f'{INSIGHTS_CLOUD_PROXY_PATH}/api/insights/v1'


def advisor_url(*segments, organization_id, base_url=None):
    """Build a fully-qualified Foreman ``insights_cloud`` Advisor API URL.

    :param segments: path segments, e.g. ``('ack',)`` or
        ``('hostack', host_ack_id)``. Each segment is URL-quoted, so values
        like a rule ID containing ``|`` are safe to pass through directly.
    :param organization_id: injected as an explicit query param (see module
        docstring).
    :param base_url: overrides the target Satellite's base URL, otherwise
        ``robottelo.config.get_url()`` is used.
    """
    path = '/'.join(quote(str(segment), safe='') for segment in segments)
    return f'{base_url or get_url()}{ADVISOR_API_PATH}/{path}/?organization_id={organization_id}'


def advisor_request_kwargs(auth=None, verify_ssl=False):
    """Common ``nailgun.client``/``requests`` kwargs for every Advisor proxy call."""
    return {
        'auth': auth or get_credentials(),
        'verify': verify_ssl,
        'headers': {'Accept': 'application/json'},
    }
