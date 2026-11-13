"""HTTP helpers for Foreman's ``insights_cloud`` Vulnerability Engine Manager proxy routes.

Foreman's ``foreman_rh_cloud`` plugin exposes Vulnerability Engine Manager routes
(CVEs, systems, vulnerabilities overview, dashboard, feature flags, playbook
templates) behind an ``/insights_cloud`` proxy that forwards to the hosted
Vulnerability API. These routes have no nailgun entity wrapper, so calls go
straight through ``nailgun.client``, the same pattern this repo already uses
elsewhere for non-entity routes (see ``tests/foreman/api/test_activationkey.py``).

The proxy expects:

* an explicit ``organization_id`` query param on every request. Foreman's
  ``ApplicationController`` (which the proxy's ``UIRequestsController``
  inherits) falls back to ``params[:organization_id]`` when no browser-session
  organization is set (see ``find_user_taxonomy`` in Foreman core's
  ``application_controller.rb``), which is what makes this work for a
  token-authenticated caller that never has a browser session. This param is
  Foreman-internal only: ``foreman_rh_cloud`` resolves it into an
  ``Organization``, then forwards org scoping downstream via an ``X-Org-Id``
  header (``CertAuth#execute_cloud_request``), never as a forwarded query
  param -- the Vulnerability Engine Manager backend's strict OpenAPI
  validation rejects any undeclared query param, so ``organization_id``
  itself must not leak past Foreman;
* Foreman's own HTTP basic auth (``robottelo.config.get_credentials()``), not
  a hosted ``x-rh-identity`` header;
* an explicit ``Accept: application/json`` header. Without it, Foreman's
  catch-all router returns a 200 with its HTML app shell instead of
  forwarding to the JSON API, since nothing else in a plain Basic-Auth
  request signals that JSON (not the web UI) is wanted;
* an explicit ``Content-Type: application/vnd.api+json`` header on every
  request (GET included -- harmless there, required for PATCH/POST). The
  Vulnerability Engine Manager backend is a JSON:API service and rejects a
  plain ``application/json`` body content type with ``415``.

Paths are built *without* a trailing slash (unlike the Advisor ack/hostack
routes): Foreman's ``insights_cloud`` catch-all route doesn't match a
trailing-slash-terminated path at all, returning a routing-level 404 before
ever reaching ``UIRequestsController``.
"""

from urllib.parse import quote

from robottelo.config import get_credentials, get_url, settings

INSIGHTS_CLOUD_PROXY_PATH = '/insights_cloud'
VULNERABILITY_API_PATH = f'{INSIGHTS_CLOUD_PROXY_PATH}/api/vulnerability/v1'


def vulnerability_url(*segments, organization_id=None, base_url=None):
    """Build a fully-qualified Foreman ``insights_cloud`` Vulnerability API URL.

    :param segments: path segments, e.g. ``('systems',)`` or
        ``('systems', inventory_id, 'cves')``. Each segment is URL-quoted, so
        values like a rule ID containing ``|`` are safe to pass through
        directly.
    :param organization_id: injected as an explicit query param (see module
        docstring). Omit it (leave as ``None``) to build a request with no
        organization context at all -- for a token-authenticated caller this
        is expected to 400, not fall back to a default organization (see the
        org-scoping tests below).
    :param base_url: overrides the target Satellite's base URL, otherwise
        ``robottelo.config.get_url()`` is used.
    """
    path = '/'.join(quote(str(segment), safe='') for segment in segments)
    url = f'{base_url or get_url()}{VULNERABILITY_API_PATH}/{path}'
    if organization_id is not None:
        url += f'?organization_id={organization_id}'
    return url


def vulnerability_request_kwargs(auth=None, verify_ssl=None):
    """Common ``nailgun.client``/``requests`` kwargs for every Vulnerability proxy call."""
    return {
        'auth': auth or get_credentials(),
        'verify': settings.server.verify_ca if verify_ssl is None else verify_ssl,
        # lowercase key required: nailgun.client's content-type auto-default
        # check (`'content-type' in kwargs['headers']`) is case-sensitive, so
        # a capitalized 'Content-Type' key here would be silently shadowed by
        # nailgun adding its own lowercase 'content-type': 'application/json'
        # alongside it.
        'headers': {'Accept': 'application/json', 'content-type': 'application/vnd.api+json'},
    }
