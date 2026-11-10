"""Regression tests for Content View filter rule authorization (CVE-2026-81668).

Covers the object-level authorization bypass in the Content View Filter Rules
API, where the parent filter was resolved without the user's organization
scope, allowing a user with Content View permissions in one organization to
access and modify filter rules belonging to another organization.

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Artemis

:CaseImportance: Critical

"""

from fauxfactory import gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.config import user_nailgun_config

# Correct authorization denials on this endpoint are 403 (permission denied)
# or 404 (out-of-scope resource hidden), per the security tracker.
# Authentication (401), validation (422) or server (5xx) errors do not count.
DENIED_STATUS_CODES = (403, 404)


def _create_user(target_sat, orgs, permission_names):
    """Create a non-admin user with the given CV permissions scoped to orgs.

    Returns a nailgun server config authenticating as the created user.
    """
    permissions = target_sat.api.Permission().search(
        query={'search': 'resource_type="Katello::ContentView"'}
    )
    permissions = [p for p in permissions if p.name in permission_names]
    assert len(permissions) == len(permission_names), (
        f'Expected permissions {permission_names} not found on server'
    )
    role = target_sat.api.Role().create()
    target_sat.api.Filter(organization=list(orgs), permission=permissions, role=role).create()
    login = gen_string('alpha')
    password = gen_string('alphanumeric')
    target_sat.api.User(
        admin=False,
        organization=list(orgs),
        role=[role],
        login=login,
        password=password,
    ).create()
    return user_nailgun_config(login, password)


def _make_filter_with_rule(target_sat, org):
    """Create a content view with an RPM filter holding one package rule."""
    content_view = target_sat.api.ContentView(organization=org).create()
    cv_filter = target_sat.api.RPMContentViewFilter(content_view=content_view).create()
    rule = target_sat.api.ContentViewFilterRule(
        content_view_filter=cv_filter, name=gen_string('alphanumeric')
    ).create()
    return content_view, cv_filter, rule


def _rule_names(target_sat, cv_filter):
    """Return the names of all rules on a filter, as administrator."""
    rules = target_sat.api.ContentViewFilterRule(content_view_filter=cv_filter).search()
    return sorted(rule.name for rule in rules)


def _assert_denied(exc_info, user_label, operation):
    """Assert an HTTPError is an authorization denial, not another failure."""
    error = exc_info.value
    status = error.response.status_code
    assert status in DENIED_STATUS_CODES, (
        f'{user_label}: {operation} must be denied with one of '
        f'{DENIED_STATUS_CODES}, got HTTP {status}: {error.response.text[:200]}'
    )


@pytest.fixture
def cv_filter_rules_env(target_sat, module_org, function_org):
    """Two-organization Content View filter rule environment.

    OrgA (module_org) holds OwnCV/filter-A/rule-A, OrgB (function_org) holds
    SecretCV/filter-B/rule-B. Users (each with a single scoped role):
        editor-A: view + edit content views, member of OrgA only
        reader-A: view content views only, member of OrgA only
    """
    own_cv, filter_a, rule_a = _make_filter_with_rule(target_sat, module_org)
    secret_cv, filter_b, rule_b = _make_filter_with_rule(target_sat, function_org)

    return {
        'filter_a': filter_a,
        'rule_a': rule_a,
        'secret_cv_id': secret_cv.id,
        'filter_b': filter_b,
        'rule_b': rule_b,
        'editor_a_cfg': _create_user(
            target_sat, [module_org], ['view_content_views', 'edit_content_views']
        ),
        'reader_a_cfg': _create_user(target_sat, [module_org], ['view_content_views']),
    }


def test_positive_content_view_filter_rules_reject_cross_org_access(
    target_sat, cv_filter_rules_env
):
    """Cross-organization rule access and modification are blocked.

    :id: 3f1c8a92-6d47-4f2b-9c15-a7d0c4e6b1aa

    :steps:

        1. As editor-A (view+edit in OrgA only), list rules of own-org
           filter-A and confirm it succeeds.
        2. Confirm OrgB's content view cannot be retrieved.
        3. Attempt to list, view, create, update and delete rules on OrgB's
           filter-B using its known IDs.
        4. After each write attempt, inspect OrgB as administrator and
           confirm no state change persisted.

    :expectedresults: All cross-organization operations are denied and no
        rule on OrgB's filter is created, modified or deleted.

    :CaseImportance: Critical
    """
    env = cv_filter_rules_env
    cfg = env['editor_a_cfg']
    filter_b, rule_b = env['filter_b'], env['rule_b']
    baseline = _rule_names(target_sat, filter_b)

    # 1. Authorized operation in own organization succeeds.
    rules = target_sat.api.ContentViewFilterRule(
        server_config=cfg, content_view_filter=env['filter_a']
    ).search()
    assert any(rule.id == env['rule_a'].id for rule in rules), (
        'editor-A must be able to list rules of own-org filter-A'
    )

    # 2. OrgB's content view itself is not retrievable.
    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentView(server_config=cfg, id=env['secret_cv_id']).read()
    _assert_denied(exc_info, 'editor-A', 'read OrgB content view')

    # 3. Cross-organization rule operations on filter-B using known IDs.
    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=cfg, content_view_filter=filter_b
        ).search()
    _assert_denied(exc_info, 'editor-A', 'list OrgB filter rules')

    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=cfg, id=rule_b.id, content_view_filter=filter_b
        ).read()
    _assert_denied(exc_info, 'editor-A', 'view OrgB filter rule')

    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=cfg, content_view_filter=filter_b, name='should-not-work'
        ).create()
    _assert_denied(exc_info, 'editor-A', 'create OrgB filter rule')
    # 4. Create attempt persisted nothing.
    assert _rule_names(target_sat, filter_b) == baseline, (
        'Cross-org create must not persist a rule on OrgB filter-B'
    )

    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=cfg,
            id=rule_b.id,
            content_view_filter=filter_b,
            name='should-not-work-either',
        ).update(['name'])
    _assert_denied(exc_info, 'editor-A', 'update OrgB filter rule')
    # Update attempt changed nothing.
    unchanged = target_sat.api.ContentViewFilterRule(
        id=rule_b.id, content_view_filter=filter_b
    ).read()
    assert unchanged.name == rule_b.name, (
        f'Cross-org update must not modify OrgB rule: '
        f'expected {rule_b.name!r}, found {unchanged.name!r}'
    )

    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=cfg, id=rule_b.id, content_view_filter=filter_b
        ).delete()
    _assert_denied(exc_info, 'editor-A', 'delete OrgB filter rule')
    # Delete attempt removed nothing.
    assert _rule_names(target_sat, filter_b) == baseline, (
        'Cross-org delete must not remove OrgB rule'
    )


def test_positive_content_view_filter_rules_enforce_read_and_edit_scopes(
    target_sat, cv_filter_rules_env
):
    """Authorized access and read/edit scope separation work.

    :id: 8b4d2e17-95a3-4c60-b1e8-2f9a6d3c7e55

    :steps:

        1. As editor-A (view+edit in OrgA): list/view OrgA rules succeed;
           create, update and delete a disposable rule succeed and persist.
        2. As reader-A (view only in OrgA): list/view succeed; create,
           update and delete are denied; administrator confirms no change.

    :expectedresults: Authorized operations succeed and persist; write
        operations without the edit permission are denied without
        persisting changes.

    :CaseImportance: Critical
    """
    env = cv_filter_rules_env
    filter_a, rule_a = env['filter_a'], env['rule_a']

    # --- A. editor-A on OrgA: full authorized CRUD ---------------------
    editor_cfg = env['editor_a_cfg']
    rules = target_sat.api.ContentViewFilterRule(
        server_config=editor_cfg, content_view_filter=filter_a
    ).search()
    assert any(rule.id == rule_a.id for rule in rules)
    target_sat.api.ContentViewFilterRule(
        server_config=editor_cfg, id=rule_a.id, content_view_filter=filter_a
    ).read()

    disposable = target_sat.api.ContentViewFilterRule(
        server_config=editor_cfg,
        content_view_filter=filter_a,
        name=gen_string('alphanumeric'),
    ).create()
    assert (
        target_sat.api.ContentViewFilterRule(id=disposable.id, content_view_filter=filter_a)
        .read()
        .name
        == disposable.name
    ), 'editor-A create must persist in OrgA'

    new_name = gen_string('alphanumeric')
    target_sat.api.ContentViewFilterRule(
        server_config=editor_cfg,
        id=disposable.id,
        content_view_filter=filter_a,
        name=new_name,
    ).update(['name'])
    assert (
        target_sat.api.ContentViewFilterRule(id=disposable.id, content_view_filter=filter_a)
        .read()
        .name
        == new_name
    ), 'editor-A update must persist in OrgA'

    target_sat.api.ContentViewFilterRule(
        server_config=editor_cfg, id=disposable.id, content_view_filter=filter_a
    ).delete()
    with pytest.raises(HTTPError):
        target_sat.api.ContentViewFilterRule(id=disposable.id, content_view_filter=filter_a).read()

    # --- B. reader-A on OrgA: read allowed, writes denied --------------
    reader_cfg = env['reader_a_cfg']
    rules = target_sat.api.ContentViewFilterRule(
        server_config=reader_cfg, content_view_filter=filter_a
    ).search()
    assert any(rule.id == rule_a.id for rule in rules), (
        'reader-A must be able to list rules of readable OrgA filter-A'
    )
    target_sat.api.ContentViewFilterRule(
        server_config=reader_cfg, id=rule_a.id, content_view_filter=filter_a
    ).read()

    baseline_a = _rule_names(target_sat, filter_a)
    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=reader_cfg,
            content_view_filter=filter_a,
            name=gen_string('alphanumeric'),
        ).create()
    _assert_denied(exc_info, 'reader-A', 'create OrgA filter rule')
    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=reader_cfg,
            id=rule_a.id,
            content_view_filter=filter_a,
            name=gen_string('alphanumeric'),
        ).update(['name'])
    _assert_denied(exc_info, 'reader-A', 'update OrgA filter rule')
    with pytest.raises(HTTPError) as exc_info:
        target_sat.api.ContentViewFilterRule(
            server_config=reader_cfg, id=rule_a.id, content_view_filter=filter_a
        ).delete()
    _assert_denied(exc_info, 'reader-A', 'delete OrgA filter rule')
    assert _rule_names(target_sat, filter_a) == baseline_a, (
        'reader-A denied writes must not change OrgA filter-A rules'
    )
