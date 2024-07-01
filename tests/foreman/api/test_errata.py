"""API Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseComponent: ErrataManagement

:team: Phoenix-content

:CaseImportance: High

"""

# For ease of use hc refers to host-collection throughout this document
from time import sleep, time

import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_CV,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE_NAME,
    FAKE_4_CUSTOM_PACKAGE,
    FAKE_4_CUSTOM_PACKAGE_NAME,
    FAKE_5_CUSTOM_PACKAGE,
    FAKE_9_YUM_OUTDATED_PACKAGES,
    FAKE_9_YUM_SECURITY_ERRATUM,
    FAKE_9_YUM_UPDATED_PACKAGES,
    PRDS,
    REAL_RHEL8_1_ERRATA_ID,
    REAL_RHEL8_1_PACKAGE_FILENAME,
    REPOS,
    REPOSET,
)

pytestmark = [
    pytest.mark.run_in_one_thread,
    pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    ),
]

CUSTOM_REPO_URL = settings.repos.yum_9.url
CUSTOM_REPO_ERRATA_ID = settings.repos.yum_6.errata[2]
ERRATA = [
    {
        'id': settings.repos.yum_6.errata[2],  # security advisory
        'old_package': FAKE_1_CUSTOM_PACKAGE,
        'new_package': FAKE_2_CUSTOM_PACKAGE,
        'package_name': FAKE_2_CUSTOM_PACKAGE_NAME,
    },
    {
        'id': settings.repos.yum_6.errata[0],  # bugfix advisory
        'old_package': FAKE_4_CUSTOM_PACKAGE,
        'new_package': FAKE_5_CUSTOM_PACKAGE,
        'package_name': FAKE_4_CUSTOM_PACKAGE_NAME,
    },
]
REPO_WITH_ERRATA = {
    'url': settings.repos.yum_9.url,
    'errata': ERRATA,
    'errata_ids': settings.repos.yum_9.errata,
}


@pytest.fixture(scope='module')
def activation_key(module_sca_manifest_org, module_cv, module_lce, module_target_sat):
    """A new Activation Key associated with published version
    of module_cv, promoted to module_lce."""
    _cv = cv_publish_promote(
        module_target_sat,
        module_sca_manifest_org,
        module_cv,
        module_lce,
    )['content-view']
    return module_target_sat.api.ActivationKey(
        organization=module_sca_manifest_org,
        environment=module_lce,
        content_view=_cv,
    ).create()


@pytest.fixture(scope='module')
def rh_repo(module_sca_manifest_org, module_lce, module_cv, activation_key, module_target_sat):
    "rhel8 rh repos with errata and outdated/updated packages"
    return module_target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst8'],
            'repository': REPOS['rhst8']['name'],
            'organization-id': module_sca_manifest_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': activation_key.id,
        },
    )


@pytest.fixture(scope='module')
def custom_repo(module_sca_manifest_org, module_lce, module_cv, activation_key, module_target_sat):
    "zoo repos with errata and outdated/updated packages"
    return module_target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': CUSTOM_REPO_URL,
            'organization-id': module_sca_manifest_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': activation_key.id,
        }
    )


def _validate_errata_counts(host, errata_type, expected_value, timeout=120):
    """Check whether host contains expected errata counts."""
    for _ in range(timeout // 5):
        host = host.read()
        if host.content_facet_attributes['errata_counts'][errata_type] == expected_value:
            break
        sleep(5)
    else:
        pytest.fail(
            'Host {} contains {} {} errata, but expected to contain {} of them'.format(
                host.name,
                host.content_facet_attributes['errata_counts'][errata_type],
                errata_type,
                expected_value,
            )
        )


def _fetch_library_environment_for_org(sat, org):
    search = {'search': f'name="Library" and organization_id={org.id}'}
    return sat.api.LifecycleEnvironment().search(query=search)[0].read()


def _fetch_available_errata(host, expected_amount=None, timeout=120):
    """Fetch available errata for host."""
    errata = host.errata()
    for _ in range(timeout // 5):
        if expected_amount is None:
            return errata['results']
        if len(errata['results']) == expected_amount:
            return errata['results']
        sleep(5)
        errata = host.errata()
    else:
        pytest.fail(
            'Host {} contains {} available errata, but expected to contain {} of them'.format(
                host.name,
                len(errata['results']),
                expected_amount if not None else 'No expected_amount provided',
            )
        )


def _fetch_available_errata_instances(sat, host, expected_amount=None, timeout=120):
    """Fetch list of instances of avaliable errata for host."""
    _errata_dict = _fetch_available_errata(host.nailgun_host, expected_amount, timeout)
    _errata_ids = [errata['id'] for errata in _errata_dict]
    instances = [sat.api.Errata(id=_id).read() for _id in _errata_ids]
    assert (
        len(instances) == len(_errata_dict) == host.applicable_errata_count
    ), 'Length of errata instances list or api result differs from expected applicable count.'
    return instances


def errata_id_set(erratum_list):
    """Return a set of unique errata id's, passing list of errata instances, or dictionary.
    :raise: `AssertionError`: if errata_id could not be found from a list entry.
    :return: set{string}
    """
    result = set()
    try:
        # erratum_list is a list of errata instances
        result = set(e.errata_id for e in erratum_list)
    except Exception:
        try:
            # erratum_list is a list of errata dictionary references
            result = set(e['errata_id'] for e in erratum_list)
        except Exception as err:
            # some errata_id cannot be extracted from an entry in erratum_list
            raise AssertionError(
                'Must take a dictionary ref or list of erratum instances, each entry needs attribute or key "errata_id".'
                f' An entry in the given erratum_list had no discernible "errata_id". Errata(s): {erratum_list}.'
            ) from err
    return result


def package_applicability_changed_as_expected(
    sat,
    host,
    package_filename,
    prior_applicable_errata_list,
    prior_applicable_errata_count,
    prior_applicable_package_count,
    return_applicables=False,
):
    """Checks that installing some package, updated any impacted errata(s)
    status and host applicability count, and changed applicable package count by one.

    That one of the following occured:
    - A non-applicable package was modified, or the same prior version was installed,
        the amount of applicable errata and applicable packages remains the same.
        Return False, as no applicability changes occured.

    - An Outdated applicable package was installed. Errata applicability increased
        by the number of found applicable errata containing that package,
            if the errata were not already applicable prior to install.
        The number of applicable packages increased by one.

    - An Updated applicable package was installed. Errata applicability decreased
        by the amount of found errata containing that package, if the errata are
            no longer applicable, but they were prior to install, if any.
        The number of applicable packages decreased by one.

    :param string: package_filename:
        the full filename of the package version installed.
    :param list: prior_applicable_errata_list:
        list of all erratum instances from search, that were applicable before modifying package.
    :param int prior_applicable_errata_count:
        number of total applicable errata prior to modifying package.
    :param int prior_applicable_package_count:
        number of total applicable packages prior to modifying package.
    :param boolean return_applicables (False): if set to True, and method's 'result' is not False:
        return a dict containing result, and relevant package and errata information.

    :raise: `AssertionError` if:
        Expected changes are not found.
        Changes are made to unexpected errata or packages.
        A non-readable prior list of erratum was passed.
    :return: result(boolean), or relevant applicables(dict)
        False if found that no applicable package was modified.
        True if method finished executing, expected changes were found.
        :return_applicables: is True: return dict of relevant applicable and changed entities:
            result boolean: True, method finished executing
            errata_count int: current applicable errata count
            package_count int: current applicable package count
            current_package string: current version filename of package
            prior_package string: previous version filename of package
            change_in_errata int: positive, negative, or zero
            changed_errata list[string]: of modified errata_ids
    """
    assert (
        len(prior_applicable_errata_list) == prior_applicable_errata_count
    ), 'Length of "prior_applicable_errata_list" passed, must equal "prior_applicable_errata_count" passed.'
    if len(prior_applicable_errata_list) != 0:
        try:
            prior_applicable_errata_list[0].read()
        except Exception as err:
            raise AssertionError(
                'Exception on read of index zero in passed parameter "prior_applicable_errata_list".'
                ' Must pass a list of readable erratum instances, or empty list.'
            ) from err
    # schedule errata applicability recalculate for most current status
    task = None
    epoch_timestamp = int(time() - 1)
    output = host.execute('subscription-manager repos')
    assert (
        output.status == 0
    ), f'Command "$subscription-manager repos" failed to execute on host: {host.hostname}'
    try:
        task = sat.api_factory.wait_for_errata_applicability_task(
            host_id=host.nailgun_host.id,
            from_when=epoch_timestamp,
        )
    except AssertionError:
        # No task for forced applicability regenerate,
        # applicability was already up to date
        assert task is None
    package_basename = str(package_filename.split("-", 1)[0])  # 'package-4.0-1.rpm' > 'package'
    prior_unique_errata_ids = errata_id_set(prior_applicable_errata_list)
    current_applicable_errata = _fetch_available_errata_instances(sat, host)
    app_unique_errata_ids = errata_id_set(current_applicable_errata)
    app_errata_with_package_diff = []
    app_errata_diff_ids = set()

    if prior_applicable_errata_count == host.applicable_errata_count:
        # Applicable errata count had no change.
        # we expect applicable errata id(s) from search also did not change.
        assert (
            prior_unique_errata_ids == app_unique_errata_ids
        ), 'Expected list of applicable erratum to remain the same.'
        if prior_applicable_package_count == host.applicable_package_count:
            # no applicable packages were modified
            return False

    if prior_applicable_errata_count != host.applicable_errata_count:
        # Modifying package changed errata applicability.
        # we expect one or more errata id(s) from search to be added or removed.
        difference = abs(prior_applicable_errata_count - host.applicable_errata_count)
        # Check list of errata id(s) from search matches expected difference
        assert (
            len(app_unique_errata_ids) == prior_applicable_errata_count + difference
        ), 'Length of applicable errata found by search, does not match applicability count difference.'
        # modifying package increased errata applicability count (outdated ver installed)
        if prior_applicable_errata_count < host.applicable_errata_count:
            # save the new errata(s) found, ones added since package modify
            app_errata_with_package_diff = [
                errata
                for errata in current_applicable_errata
                if (
                    any(package_basename in p for p in errata.packages)
                    and errata.errata_id not in prior_unique_errata_ids
                )
            ]
        # modifying package decreased errata applicability count (updated ver installed)
        elif prior_applicable_errata_count > host.applicable_errata_count:
            # save the old errata(s) found, ones removed since package modify
            app_errata_with_package_diff = [
                errata
                for errata in current_applicable_errata
                if (
                    not any(package_basename in p.filename for p in errata.packages)
                    and errata.errata_id in prior_unique_errata_ids
                )
            ]
        app_errata_diff_ids = errata_id_set(app_errata_with_package_diff)
        assert len(app_errata_diff_ids) > 0, (
            f'Applicable errata count changed by {difference}, after modifying {package_filename},'
            ' but could not find any affected errata(s) with packages list'
            f' that contains a matching package_basename: {package_basename}.'
        )
    # Check that applicable_package_count changed,
    # if not, an applicable package was not modified.
    if prior_applicable_package_count == host.applicable_package_count:
        # if applicable packages remains the same, errata should also be the same
        assert prior_applicable_errata_count == host.applicable_errata_count
        assert prior_unique_errata_ids == app_unique_errata_ids
        return False
    # is current errata list different from one prior to package install ?
    if app_unique_errata_ids != prior_unique_errata_ids:
        difference = len(app_unique_errata_ids) - len(prior_unique_errata_ids)
        # check diff in applicable counts, is equal to diff in length of errata search results.
        assert prior_applicable_errata_count + difference == host.applicable_errata_count

    """ Check applicable_package count changed by one.
        we expect applicable_errata_count increased/decrease,
        only by number of 'new' or 'removed' applicable errata, if any.
    """
    if app_errata_with_package_diff:
        if host.applicable_errata_count > prior_applicable_errata_count:
            """Current applicable errata count is higher than before install,
            An outdated package is expected to have been installed.
            Check applicable package count increased by one.
            Check applicable errata count increased by number
                of newly applicable errata.
            """
            assert prior_applicable_package_count + 1 == host.applicable_package_count
            expected_increase = 0
            if app_unique_errata_ids != prior_unique_errata_ids:
                difference = len(app_unique_errata_ids) - prior_applicable_errata_count
                assert prior_applicable_errata_count + difference == host.applicable_errata_count
                expected_increase = len(app_errata_diff_ids)
            assert prior_applicable_errata_count + expected_increase == host.applicable_errata_count

        elif host.applicable_errata_count < prior_applicable_errata_count:
            """Current applicable errata count is lower than before install,
            An updated package is expected to have been installed.
            Check applicable package count decreased by one.
            Check applicable errata count decreased by number of
               prior applicable errata, that are no longer found.
            """
            if host.applicable_errata_count < prior_applicable_errata_count:
                assert host.applicable_package_count == prior_applicable_package_count - 1
                expected_decrease = 0
                if app_unique_errata_ids != prior_unique_errata_ids:
                    difference = len(app_unique_errata_ids) - len(prior_applicable_errata_count)
                assert prior_applicable_errata_count + difference == host.applicable_errata_count
                expected_decrease = len(app_errata_diff_ids)
            assert prior_applicable_errata_count - expected_decrease == host.applicable_errata_count
        else:
            # We found by search an errata that was added or removed compared to prior install,
            # But we also found that applicable_errata_count had not changed.
            raise AssertionError(
                f'Found one or more different errata: {app_errata_diff_ids},'
                ' from those present prior to install, but applicable count did not change'
                f' as expected: {host.applicable_errata_count}.'
            )
    else:
        # already checked that applicable package count changed,
        # but found applicable erratum list should not change,
        # check the errata count and list remained the same.
        assert (
            host.applicable_errata_count == prior_applicable_errata_count
        ), 'Expected current applicable errata count, to equal prior applicable errata count.'
        assert (
            len(current_applicable_errata) == prior_applicable_errata_count
        ), 'Expected current applicable errata list length, to equal to prior applicable count.'
        assert prior_unique_errata_ids == app_unique_errata_ids, (
            f'Expected set of prior applicable errata_ids: {prior_unique_errata_ids},'
            f' to be equivalent to set of current applicable errata_ids: {app_unique_errata_ids}.'
        )
    if return_applicables is True:
        change_in_errata = len(app_unique_errata_ids) - prior_applicable_errata_count
        output = host.execute(f'rpm -q {package_basename}').stdout
        current_package = output[:-1]
        assert package_basename in current_package
        if current_package == package_filename:  # noqa: SIM108
            # we have already checked if applicable package count changed,
            # in case the same version as prior was installed and present.
            prior_package = None  # package must not have been present before this modification
        else:
            prior_package = package_filename
        return {
            'result': True,
            'errata_count': host.applicable_errata_count,
            'package_count': host.applicable_package_count,
            'current_package': current_package,
            'prior_package': prior_package,
            'change_in_errata': change_in_errata,
            'changed_errata': list(app_errata_diff_ids),
        }
    return True


def cv_publish_promote(sat, org, cv, lce=None, needs_publish=True, force=False):
    """Publish & promote Content View Version with all content visible in org.

    :param lce: if None, default to 'Library',
        pass a single environment :id or instance.
        Or pass a list of environment :ids or isntances.
    :param bool needs_publish: if False, skip publish of a new version
    :return dictionary:
        'content-view': instance of updated cv
        'content-view-version': instance of newest cv version
    """
    # Default to 'Library' lce, if None passed
    # Take a single lce id, of list of ids
    # or Take a single instance of lce, or list of instances
    lce_library = _fetch_library_environment_for_org(sat, org)
    lce_ids = [lce_library.id]
    if lce is not None:
        if not isinstance(lce, list):
            # a list was not passed, just single id or lce
            lce_ids = [lce] if isinstance(lce, int) else [lce.id]
        else:
            # a list of ids or instances was passed
            lce_ids = lce if isinstance(lce[0], int) else [env.id for env in lce]

        for _id in lce_ids:
            # entries in list of ids now just be int
            assert isinstance(_id, int)

    # multiple ids in list, sort:
    if len(lce_ids) > 1:
        lce_ids = sorted(lce_ids)

    # Publish by default, or skip and use latest existing version
    if needs_publish is True:
        _publish_and_wait(sat, org, cv, search_rate=5, max_tries=12)
    # Content-view must have at least one published version
    cv = sat.api.ContentView(id=cv.id).read()
    assert cv.version, f'No version(s) are published to the Content-View: {cv.id}'
    # Find highest version id, will be the latest
    cvv_id = max(cvv.id for cvv in cv.version)
    # Promote to lifecycle-environment(s):
    # when we promote to other environments, 'Library'/:id should not be passed,
    # as it will be promoted to automatically.
    if len(lce_ids) > 1 and lce_library.id in lce_ids:
        # remove library.id from list if list contains more than just library
        lce_ids.remove(lce_library.id)
    if lce is None or (len(lce_ids) == 1 and lce_library.id in lce_ids):
        # only Library in list, or lce passed was None, promote only to Library,
        # promoting out of order may require force to bypass
        lce_library = lce_library.read()
        sat.api.ContentViewVersion(id=cvv_id).promote(
            data={'environment_ids': [lce_library.id], 'force': force}
        )
    else:
        # promote to any environment ids remaining in list
        sat.api.ContentViewVersion(id=cvv_id).promote(
            data={'environment_ids': lce_ids, 'force': force}
        )
    _result = {
        'content-view': sat.api.ContentView(id=cv.id).read(),
        'content-view-version': sat.api.ContentViewVersion(id=cvv_id).read(),
    }
    assert all(
        entry for entry in _result.values()
    ), f'One or more necessary components are missing: {_result}'
    return _result


def _publish_and_wait(sat, org, cv, search_rate=1, max_tries=10):
    """Publish a new version of content-view to organization, wait for task(s) completion.

    :param int: search_rate: time (seconds) in between each search for finished task(s).
    :param int: max_tries: number of searches to perform before timing out.
    """
    task_id = sat.api.ContentView(id=cv.id).publish({'id': cv.id, 'organization': org})['id']
    assert task_id, f'No task was invoked to publish the Content-View: {cv.id}.'
    # Should take < 1 minute, check in 5s intervals
    (
        sat.wait_for_tasks(
            search_query=(f'label = Actions::Katello::ContentView::Publish and id = {task_id}'),
            search_rate=search_rate,
            max_tries=max_tries,
        ),
        (
            f'Failed to publish the Content-View: {cv.id}, in time.'
            f'Task: {task_id} failed, or timed out ({search_rate*max_tries}s).'
        ),
    )


@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
@pytest.mark.no_containers
@pytest.mark.e2e
def test_positive_install_in_hc(
    module_sca_manifest_org,
    activation_key,
    module_cv,
    module_lce,
    custom_repo,
    target_sat,
    content_hosts,
):
    """Install errata in a host-collection

    :id: 6f0242df-6511-4c0f-95fc-3fa32c63a064

    :Setup:
        1. Some Unregistered hosts.
        2. Errata synced on satellite server.

    :Steps:
        1. Setup custom repo for each client, publish & promote content-view.
        2. Register clients as content hosts, install one outdated custom package on each client.
        3. Create Host Collection from clients, install errata to clients by Host Collection.
        4. PUT /api/v2/hosts/bulk/update_content

    :expectedresults:
        1. package install invokes errata applicability recalculate
        2. errata is installed in the host-collection
        3. errata installation invokes applicability recalculate
        4. updated custom package is found on the contained hosts

    :CaseImportance: Medium


    :BZ: 1983043
    """
    # custom_repo already in published a module_cv version
    repo_id = custom_repo['repository-id']
    # just promote to lce, do not publish
    cv_publish_promote(
        target_sat, module_sca_manifest_org, module_cv, module_lce, needs_publish=False
    )
    # Each client: create custom repo, register as content host to cv, install outdated package
    for client in content_hosts:
        _repo = target_sat.api.Repository(id=repo_id).read()
        client.create_custom_repos(**{f'{_repo.name}': _repo.url})
        result = client.register(
            org=module_sca_manifest_org,
            activation_keys=activation_key.name,
            target=target_sat,
            loc=None,
        )
        assert (
            result.status == 0
        ), f'Failed to register the host - {client.hostname}: {result.stderr}'
        client.add_rex_key(satellite=target_sat)
        assert client.subscribed
        client.run(r'subscription-manager repos --enable \*')
        # Remove custom package by name
        client.run(f'yum remove -y {FAKE_2_CUSTOM_PACKAGE_NAME}')
        # No applicable errata or packages to start
        assert (pre_errata_count := client.applicable_errata_count) == 0
        assert (pre_package_count := client.applicable_package_count) == 0
        prior_app_errata = _fetch_available_errata_instances(target_sat, client, expected_amount=0)
        # 1s margin of safety for rounding
        epoch_timestamp = int(time() - 1)
        # install outdated version
        assert client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
        target_sat.api_factory.wait_for_errata_applicability_task(
            host_id=client.nailgun_host.id,
            from_when=epoch_timestamp,
        )
        assert client.run(f'rpm -q {FAKE_1_CUSTOM_PACKAGE}').status == 0
        # One errata now applicable on client
        assert client.applicable_errata_count == 1
        # One package now has an applicable errata
        assert client.applicable_package_count == 1
        # Fetch the new errata instance(s), expecting only one
        _fetch_available_errata_instances(target_sat, client, expected_amount=1)

        """ Did installing outdated package, update applicability as expected?
            * Call method package_applicability_changed_as_expected *
            returns: False if no applicability change occured or expected (package not applicable).
                True if applicability changes were expected and occured (package is applicable).
            raises: `AssertionError` if any expected changes did not occur, or unexpected changes were found.

            Expected: that each outdated package install: updated one or more errata to applicable,
                if those now applicable errata(s) were not already applicable to some package prior.
        """
        passed_checks = package_applicability_changed_as_expected(
            target_sat,
            client,
            FAKE_1_CUSTOM_PACKAGE,
            prior_app_errata,
            pre_errata_count,
            pre_package_count,
        )
        assert (
            passed_checks is True
        ), f'The package: {FAKE_1_CUSTOM_PACKAGE}, was not applicable to any erratum present on host: {client.hostname}.'
    # Setup host collection using client ids
    host_collection = target_sat.api.HostCollection(organization=module_sca_manifest_org).create()
    host_ids = [client.nailgun_host.id for client in content_hosts]
    host_collection.host_ids = host_ids
    host_collection = host_collection.update(['host_ids'])
    # Install erratum to host collection
    task_id = target_sat.api.JobInvocation().run(
        data={
            'feature': 'katello_errata_install',
            'inputs': {'errata': str(CUSTOM_REPO_ERRATA_ID)},
            'targeting_type': 'static_query',
            'search_query': f'host_collection_id = {host_collection.id}',
            'organization_id': module_sca_manifest_org.id,
        },
    )['id']
    (
        target_sat.wait_for_tasks(
            search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
            search_rate=15,
            max_tries=10,
        ),
        (
            f'Could not install erratum: {CUSTOM_REPO_ERRATA_ID}, to Host-Collection.'
            f' Task: {task_id} failed, or timed out.'
        ),
    )
    for client in content_hosts:
        # No applicable errata after install on all clients
        assert (
            client.applicable_errata_count == 0
        ), f'A client in Host-Collection: {client.hostname}, had {client.applicable_errata_count} '
        'applicable errata, expected 0.'
        # Updated package is present on all clients
        result = client.run(f'rpm -q {FAKE_2_CUSTOM_PACKAGE}')
        assert result.status == 0, (
            f'The client in Host-Collection: {client.hostname},'
            f' could not find the updated package: {FAKE_2_CUSTOM_PACKAGE}'
        )
        # No applicable packages on client
        assert client.applicable_package_count == 0, (
            f'A client in Host-Collection: {client.hostname}, had {client.applicable_package_count} '
            f'applicable package(s) after installing erratum: {CUSTOM_REPO_ERRATA_ID}, but expected 0.'
        )


@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
@pytest.mark.no_containers
@pytest.mark.e2e
def test_positive_install_multiple_in_host(
    target_sat, rhel_contenthost, module_org, activation_key, module_lce
):
    """For a host with multiple applicable errata install one and ensure
    the rest of errata is still available, repeat for some list of errata.
    After each package or errata install, check applicability updates
    as expected.

    :id: 67b7e95b-9809-455a-a74e-f1815cc537fc

    :setup:
        1. An Unregistered host.
        2. Errata synced on satellite server.

    :steps:
        1. Setup content for a content host (repos, cv, etc)
        2. Register vm as a content host
        3. Remove any impacted custom packages present
            - no applicable errata to start
        4. Install outdated versions of the custom packages
            - some expected applicable errata
        5. Install any applicable security errata
            - errata applicability drops after each install
            - applicable packages drops by amount updated
            - impacted package(s) updated and found

    :expectedresults:
        1. Package installation succeeded, if the package makes a
            new errata applicable; available errata counter
            increased by one.
        2. Errata apply task succeeded, available errata
            counter decreased by one; it is possible to schedule
            another errata installation.
        3. Applicable package counter decreased by number
            of updated packages. Updated package(s) found.
        4. Errata recalculate applicability task is invoked
            automatically, after install command of applicable package,
            and errata apply task. Task(s) found and finish succesfully.

    :customerscenario: true

    :BZ: 1469800, 1528275, 1983043, 1905560

    :CaseImportance: Medium

    :parametrized: yes

    """
    # Associate custom repos with org, lce, ak:
    custom_repo_id = target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_9.url,
            'organization-id': module_org.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': activation_key.id,
        }
    )['repository-id']
    rhel_contenthost.register(
        activation_keys=activation_key.name,
        target=target_sat,
        org=module_org,
        loc=None,
    )
    assert rhel_contenthost.subscribed
    # 1s margin of safety for rounding
    epoch_timestamp = int(time() - 1)
    # Remove any packages errata could apply to, verify none are present on host
    for package in FAKE_9_YUM_OUTDATED_PACKAGES:
        pkg_name = str(package.split("-", 1)[0])  # 'bear-4.0-1.noarch' > 'bear'
        result = rhel_contenthost.run(f'yum remove -y {pkg_name}')
        assert rhel_contenthost.run(f'rpm -q {pkg_name}').status == 1

    # Wait for any recalculate task(s), possibly invoked by yum remove,
    # catch AssertionError raised if no task was generated
    try:
        target_sat.api_factory.wait_for_errata_applicability_task(
            host_id=rhel_contenthost.nailgun_host.id,
            from_when=epoch_timestamp,
        )
    except AssertionError:
        # Yum remove did not trigger any errata recalculate task,
        # assert any YUM_9 packages were/are not present, then continue
        present_packages = set(
            [
                package.filename
                for package in target_sat.api.Package(repository=custom_repo_id).search()
            ]
        )
        assert not set(FAKE_9_YUM_OUTDATED_PACKAGES).intersection(present_packages)
        assert not set(FAKE_9_YUM_UPDATED_PACKAGES).intersection(present_packages)

    # No applicable errata to start
    assert rhel_contenthost.applicable_errata_count == 0
    present_applicable_packages = []
    # Installing all YUM_9 outdated custom packages
    for i in range(len(FAKE_9_YUM_OUTDATED_PACKAGES)):
        # record params prior to install, for post-install checks
        package_filename = FAKE_9_YUM_OUTDATED_PACKAGES[i]
        FAKE_9_YUM_UPDATED_PACKAGES[i]
        pre_errata_count = rhel_contenthost.applicable_errata_count
        pre_package_count = rhel_contenthost.applicable_package_count
        prior_app_errata = _fetch_available_errata_instances(target_sat, rhel_contenthost)
        # 1s margin of safety for rounding
        epoch_timestamp = int(time() - 1)
        assert rhel_contenthost.run(f'yum install -y {package_filename}').status == 0
        # Wait for async errata recalculate task(s), invoked by yum install,
        # searching back 1s prior to install.
        target_sat.api_factory.wait_for_errata_applicability_task(
            host_id=rhel_contenthost.nailgun_host.id,
            from_when=epoch_timestamp,
        )
        # outdated package found on host
        assert rhel_contenthost.run(f'rpm -q {package_filename}').status == 0
        """
            Modifying the applicable package did all:
            1. changed package applicability count by one and only one.
            2. changed errata applicability count by number of affected errata, whose
                applicability status changed after package was modified.
            3. changed lists of applicable packages and applicable errata accordingly.
            - otherwise raise `AssertionError` in below method;
        """
        passed_checks = package_applicability_changed_as_expected(
            target_sat,
            rhel_contenthost,
            package_filename,
            prior_app_errata,
            pre_errata_count,
            pre_package_count,
        )
        # If passed_checks is False, this package was not applicable, continue to next.
        if passed_checks is True:
            present_applicable_packages.append(package_filename)

    # Some applicable errata(s) now expected for outdated packages
    assert rhel_contenthost.applicable_errata_count > 0
    # Expected applicable package(s) now for the applicable errata
    assert rhel_contenthost.applicable_package_count == len(present_applicable_packages)
    post_app_errata = _fetch_available_errata_instances(target_sat, rhel_contenthost)
    """Installing all YUM_9 security errata sequentially, if applicable.
       after each install, applicable-errata-count should drop by one,
       one or more of the erratum's listed packages should be updated.
    """
    installed_errata = []
    updated_packages = []
    expected_errata_to_install = [
        errata.errata_id
        for errata in post_app_errata
        if errata.errata_id in FAKE_9_YUM_SECURITY_ERRATUM
    ]
    all_applicable_packages = set(
        package for errata in post_app_errata for package in errata.packages
    )
    security_packages_to_install = set()
    for errata_id in FAKE_9_YUM_SECURITY_ERRATUM:
        errata_instance = (
            target_sat.api.Errata().search(query={'search': f'errata_id="{errata_id}"'})[0].read()
        )
        present_packages_impacted_by_errata = [
            package
            for package in errata_instance.packages
            if package in FAKE_9_YUM_UPDATED_PACKAGES
        ]
        security_packages_to_install.update(present_packages_impacted_by_errata)
    # Are expected security errata packages found in all applicable packages ?
    assert security_packages_to_install.issubset(all_applicable_packages)
    # Try to install each ERRATUM in FAKE_9_YUM_SECURITY_ERRATUM list,
    # Each time, check lists of applicable erratum and packages, and counts
    for ERRATUM in FAKE_9_YUM_SECURITY_ERRATUM:
        pre_errata_count = rhel_contenthost.applicable_errata_count
        ERRATUM_instance = (
            target_sat.api.Errata().search(query={'search': f'errata_id="{ERRATUM}"'})[0].read()
        )
        # Check each time before each install
        applicable_errata = _fetch_available_errata_instances(target_sat, rhel_contenthost)
        # If this ERRATUM is not applicable, continue to next
        if (len(applicable_errata) == 0) or (
            ERRATUM not in [_errata.errata_id for _errata in applicable_errata]
        ):
            continue
        assert pre_errata_count >= 1
        errata_packages = []
        pre_package_count = rhel_contenthost.applicable_package_count
        # From search result, find this ERRATUM by erratum_id,
        # save the relevant list of package(s)
        for _errata in applicable_errata:
            if _errata.errata_id == ERRATUM:
                errata_packages = _errata.packages
        assert len(errata_packages) >= 1
        epoch_timestamp = int(time() - 1)
        # Install this ERRATUM to host, wait for REX task
        task_id = target_sat.api.JobInvocation().run(
            data={
                'feature': 'katello_errata_install',
                'inputs': {'errata': str(ERRATUM)},
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel_contenthost.hostname}',
                'organization_id': module_org.id,
            },
        )['id']
        target_sat.wait_for_tasks(
            search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
            search_rate=20,
            max_tries=15,
        )
        # Wait for async errata recalculate task(s), invoked by REX task
        target_sat.api_factory.wait_for_errata_applicability_task(
            host_id=rhel_contenthost.nailgun_host.id,
            from_when=epoch_timestamp,
        )
        # Host Applicable Errata count decreased by one
        assert (
            rhel_contenthost.applicable_errata_count == pre_errata_count - 1
        ), f'Host applicable errata did not decrease by one, after installation of {ERRATUM}'
        # Applying this ERRATUM updated one or more of the erratum's listed packages
        found_updated_packages = []
        for package in errata_packages:
            result = rhel_contenthost.run(f'rpm -q {package}')
            if result.status == 0:
                assert (
                    package in FAKE_9_YUM_UPDATED_PACKAGES
                ), f'An unexpected package: "{package}", was updated by this errata: {ERRATUM}.'
                if package in ERRATUM_instance.packages:
                    found_updated_packages.append(package)

        assert len(found_updated_packages) > 0, (
            f'None of the expected errata.packages: {errata_packages}, were found on host: "{rhel_contenthost.hostname}",'
            f' after installing the applicable errata: {ERRATUM}.'
        )
        # Host Applicable Packages count dropped by number of packages updated
        assert rhel_contenthost.applicable_package_count == pre_package_count - len(
            found_updated_packages
        ), (
            f'Host: "{rhel_contenthost.hostname}" applicable package count did not decrease by {len(found_updated_packages)},'
            f' after errata: {ERRATUM} installed updated packages: {found_updated_packages}'
        )
        installed_errata.append(ERRATUM)
        updated_packages.extend(found_updated_packages)

    # In case no ERRATUM in list are applicable:
    # Lack of any package or errata install will raise `AssertionError`.
    assert (
        len(installed_errata) > 0
    ), f'No applicable errata were found or installed from list: {FAKE_9_YUM_SECURITY_ERRATUM}.'
    assert (
        len(updated_packages) > 0
    ), f'No applicable packages were found or installed from list: {FAKE_9_YUM_UPDATED_PACKAGES}.'
    # Each expected erratum and packages installed only once
    pkg_set = set(updated_packages)
    errata_set = set(installed_errata)
    assert len(pkg_set) == len(
        updated_packages
    ), f'Expect no repeat packages in install list: {updated_packages}.'
    assert len(errata_set) == len(
        installed_errata
    ), f'Expected no repeat errata in install list: {installed_errata}.'
    # Only the expected YUM_9 packages were installed
    assert set(updated_packages).issubset(set(FAKE_9_YUM_UPDATED_PACKAGES))
    # Only the expected YUM_9 errata were updated
    assert set(installed_errata).issubset(set(FAKE_9_YUM_SECURITY_ERRATUM))
    # Check number of installed errata id(s) matches expected
    assert len(installed_errata) == len(expected_errata_to_install), (
        f'Expected to install {len(expected_errata_to_install)} errata from list: {FAKE_9_YUM_SECURITY_ERRATUM},'
        f' but installed: {len(installed_errata)}.'
    )
    # Check sets of installed errata id(s) strings, matches expected
    assert set(installed_errata) == set(
        expected_errata_to_install
    ), 'Expected errata id(s) and installed errata id(s) are not the same.'
    # Check number of updated package version filename(s) matches expected
    assert len(updated_packages) == len(security_packages_to_install), (
        f'Expected to install {len(security_packages_to_install)} packages from list: {FAKE_9_YUM_UPDATED_PACKAGES},'
        f' but installed {len(updated_packages)}.'
    )
    # Check sets of installed package filename(s) strings, matches expected
    assert (
        set(updated_packages) == set(security_packages_to_install)
    ), 'Expected package version filename(s) and installed package version filenam(s) are not the same.'


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_list_sorted_filtered(custom_repo, target_sat):
    """View, sort, and filter all errata specific to repository.

    :id: 1efceabf-9821-4804-bacf-2213ac0c7550

    :Setup: Errata synced on satellite server.

    :Steps:

        1. Create two repositories each synced and containing errata
        2. GET /katello/api/errata

    :expectedresults:

        1. Check that the errata belonging to one repo is not
            showing in the other.
        2. Check that the errata can be sorted by updated date,
            issued date, and filtered by CVE.

    """
    repo1 = target_sat.api.Repository(id=custom_repo['repository-id']).read()
    repo2 = target_sat.api.Repository(
        product=target_sat.api.Product().create(), url=settings.repos.yum_3.url
    ).create()
    repo2.sync()
    repo1_errata_ids = [
        errata['errata_id'] for errata in repo1.errata(data={'per_page': '1000'})['results']
    ]
    repo2_errata_ids = [
        errata['errata_id'] for errata in repo2.errata(data={'per_page': '1000'})['results']
    ]
    # Check errata are viewable, errata for one repo is not showing in the other
    assert len(repo1_errata_ids) == len(settings.repos.yum_9.errata)
    assert len(repo2_errata_ids) == len(settings.repos.yum_3.errata)
    assert CUSTOM_REPO_ERRATA_ID in repo1_errata_ids
    assert CUSTOM_REPO_ERRATA_ID not in repo2_errata_ids
    assert settings.repos.yum_3.errata[5] in repo2_errata_ids
    assert settings.repos.yum_3.errata[5] not in repo1_errata_ids

    # View all errata in Org sorted by Updated
    repo = target_sat.api.Repository(id=custom_repo['repository-id']).read()
    assert repo.sync()['result'] == 'success'
    erratum_list = target_sat.api.Errata(repository=repo).search(
        query={'order': 'updated ASC', 'per_page': '1000'}
    )
    updated = [errata.updated for errata in erratum_list]
    assert updated == sorted(updated)

    # Errata is sorted by issued date.
    erratum_list = target_sat.api.Errata(repository=custom_repo['repository-id']).search(
        query={'order': 'issued ASC', 'per_page': '1000'}
    )
    issued = [errata.issued for errata in erratum_list]
    assert issued == sorted(issued)
    # Errata is filtered by CVE
    erratum_list = target_sat.api.Errata(repository=custom_repo['repository-id']).search(
        query={'order': 'cve DESC', 'per_page': '1000'}
    )
    # Most Errata won't have any CVEs. Removing empty CVEs from results
    erratum_cves = [errata.cves for errata in erratum_list if errata.cves]
    # Verifying each errata have its CVEs sorted in DESC order
    for errata_cves in erratum_cves:
        cve_ids = [cve['cve_id'] for cve in errata_cves]
        assert cve_ids == sorted(cve_ids, reverse=True)


@pytest.fixture(scope='module')
def setup_content_rhel8(
    module_sca_manifest_org,
    rh_repo_module_manifest,
    activation_key,
    module_lce,
    module_cv,
    module_target_sat,
    return_result=True,
):
    """Setup content for rhel8 content host
    Using RH SAT-TOOLS RHEL8 for sat-tools, and FAKE_YUM_9 as custom-repo.
    Published to content-view and promoted to lifecycle-environment.

    Raises `AssertionError` if one or more of the setup components read are empty.

    :return: if return_result is True: otherwise None
        A dictionary (_result) with the satellite instances of activaton-key, organization,
        content-view, lifecycle-environment, rh_repo, custom_repo.
    """
    org = module_sca_manifest_org
    # Setup Custom and RH repos
    custom_repo_id = module_target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': CUSTOM_REPO_URL,
            'organization-id': org.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': activation_key.id,
            'content-view-id': module_cv.id,
        }
    )['repository-id']
    custom_repo = module_target_sat.api.Repository(id=custom_repo_id).read()
    custom_repo.sync()
    # Sync and add RH repo
    rh_repo = module_target_sat.api.Repository(id=rh_repo_module_manifest.id).read()
    rh_repo.sync()
    module_target_sat.cli.ContentView.add_repository(
        {'id': module_cv.id, 'organization-id': org.id, 'repository-id': rh_repo.id}
    )
    _cv = cv_publish_promote(module_target_sat, org, module_cv, module_lce)
    module_cv = _cv['content-view']
    latest_cvv = _cv['content-view-version']

    _result = {
        'activation-key': activation_key.read(),
        'organization': org.read(),
        'content-view': module_cv.read(),
        'content-view-version': latest_cvv.read(),
        'lifecycle-environment': module_lce.read(),
        'rh_repo': rh_repo.read(),
        'custom_repo': custom_repo.read(),
    }
    assert all(
        entry for entry in _result.values()
    ), f'One or more necessary components are not present: {_result}'
    return _result if return_result else None


@pytest.mark.tier2
def test_positive_get_count_for_host(
    setup_content_rhel8, activation_key, rhel8_contenthost, module_target_sat
):
    """Available errata count when retrieving Host

    :id: 2f35933f-8026-414e-8f75-7f4ec048faae

    :Setup:

        1. Errata synced on satellite server.
        2. Some client host present.
        3. Some rh repo and custom repo, added to content-view.

    :Steps:

        1. Register content host
        2. Install some outdated packages
        3. GET /api/v2/hosts

    :expectedresults: The applicable errata count is retrieved.


    :parametrized: yes

    :CaseImportance: Medium
    """
    org = setup_content_rhel8['organization']
    custom_repo = setup_content_rhel8['rh_repo']
    rhel8_contenthost.create_custom_repos(**{f'{custom_repo.name}': custom_repo.url})
    result = rhel8_contenthost.register(
        org=org,
        activation_keys=activation_key.name,
        target=module_target_sat,
        loc=None,
    )
    assert (
        result.status == 0
    ), f'Failed to register the host - {rhel8_contenthost.hostname}: {result.stderr}'
    assert rhel8_contenthost.subscribed
    rhel8_contenthost.execute(r'subscription-manager repos --enable \*')
    host = rhel8_contenthost.nailgun_host.read()
    # No applicable errata to start
    assert rhel8_contenthost.applicable_errata_count == 0
    for errata in ('security', 'bugfix', 'enhancement'):
        _validate_errata_counts(host, errata_type=errata, expected_value=0)
    # One bugfix errata after installing outdated Kangaroo
    result = rhel8_contenthost.execute(f'yum install -y {FAKE_9_YUM_OUTDATED_PACKAGES[7]}')
    assert result.status == 0, f'Failed to install package {FAKE_9_YUM_OUTDATED_PACKAGES[7]}'
    _validate_errata_counts(host, errata_type='bugfix', expected_value=1)
    # One enhancement errata after installing outdated Gorilla
    result = rhel8_contenthost.execute(f'yum install -y {FAKE_9_YUM_OUTDATED_PACKAGES[3]}')
    assert result.status == 0, f'Failed to install package {FAKE_9_YUM_OUTDATED_PACKAGES[3]}'
    _validate_errata_counts(host, errata_type='enhancement', expected_value=1)
    # Install and check two outdated packages, with applicable security erratum
    # custom_repo outdated Walrus
    result = rhel8_contenthost.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status == 0, f'Failed to install package {FAKE_1_CUSTOM_PACKAGE}'
    _validate_errata_counts(host, errata_type='security', expected_value=1)
    # rh_repo outdated Puppet-agent
    result = rhel8_contenthost.execute(f'yum install -y {REAL_RHEL8_1_PACKAGE_FILENAME}')
    assert result.status == 0, f'Failed to install package {REAL_RHEL8_1_PACKAGE_FILENAME}'
    _validate_errata_counts(host, errata_type='security', expected_value=2)
    # All avaliable errata present
    assert rhel8_contenthost.applicable_errata_count == 4


@pytest.mark.upgrade
@pytest.mark.tier3
def test_positive_get_applicable_for_host(
    setup_content_rhel8, activation_key, rhel8_contenthost, target_sat
):
    """Get applicable errata ids for a host

    :id: 51d44d51-eb3f-4ee4-a1df-869629d427ac

    :Setup:

        1. Errata synced on satellite server.
        2. Some client hosts present.
        3. Some rh repo and custom repo, added to content-view.

    :Steps:

        1. Register vm as a content host
        2. Install some outdated packages
        3. GET /api/v2/hosts/:id/errata

    :expectedresults: The available errata is retrieved.

    :parametrized: yes

    :CaseImportance: Medium
    """
    org = setup_content_rhel8['organization']
    custom_repo = setup_content_rhel8['rh_repo']

    rhel8_contenthost.create_custom_repos(**{f'{custom_repo.name}': custom_repo.url})
    result = rhel8_contenthost.register(
        activation_keys=activation_key.name,
        target=target_sat,
        org=org,
        loc=None,
    )
    assert (
        result.status == 0
    ), f'Failed to register the host - {rhel8_contenthost.hostname}: {result.stderr}'
    assert rhel8_contenthost.subscribed
    rhel8_contenthost.execute(r'subscription-manager repos --enable \*')
    for errata in REPO_WITH_ERRATA['errata']:
        # Remove custom package if present, old or new.
        package_name = errata['package_name']
        result = rhel8_contenthost.execute(f'yum erase -y {package_name}')
        if result.status != 0:
            pytest.fail(f'Failed to remove {package_name}: {result.stdout} {result.stderr}')

    rhel8_contenthost.execute('subscription-manager repos')
    assert rhel8_contenthost.applicable_errata_count == 0
    host = rhel8_contenthost.nailgun_host.read()
    # Check no applicable errata to start
    erratum = _fetch_available_errata(host, expected_amount=0)
    assert len(erratum) == 0
    # Install outdated applicable custom package
    rhel8_contenthost.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    erratum = _fetch_available_errata(host, 1)
    assert len(erratum) == 1
    assert CUSTOM_REPO_ERRATA_ID in [errata['errata_id'] for errata in erratum]
    # Install outdated applicable real package (from RH repo)
    rhel8_contenthost.run(f'yum install -y {REAL_RHEL8_1_PACKAGE_FILENAME}')
    erratum = _fetch_available_errata(host, 2)
    assert len(erratum) == 2
    assert REAL_RHEL8_1_ERRATA_ID in [errata['errata_id'] for errata in erratum]


@pytest.mark.tier3
def test_positive_get_diff_for_cv_envs(target_sat):
    """Generate a difference in errata between a set of environments
    for a content view

    :id: 96732506-4a89-408c-8d7e-f30c8d469769

    :Setup:

        1. Errata synced on satellite server.
        2. Multiple environments present.

    :Steps: GET /katello/api/compare

    :expectedresults: Difference in errata between a set of environments
        for a content view is retrieved.

    """
    org = target_sat.api.Organization().create()
    env = target_sat.api.LifecycleEnvironment(organization=org).create()
    content_view = target_sat.api.ContentView(organization=org).create()
    activation_key = target_sat.api.ActivationKey(environment=env, organization=org).create()
    # Published content-view-version with repos will be created
    for repo_url in [settings.repos.yum_9.url, CUSTOM_REPO_URL]:
        target_sat.cli_factory.setup_org_for_a_custom_repo(
            {
                'url': repo_url,
                'organization-id': org.id,
                'content-view-id': content_view.id,
                'lifecycle-environment-id': env.id,
                'activationkey-id': activation_key.id,
            }
        )
    new_env = target_sat.api.LifecycleEnvironment(organization=org, prior=env).create()
    # no need to publish a new version, just promote newest
    cv_publish_promote(
        sat=target_sat, org=org, cv=content_view, lce=[env, new_env], needs_publish=False
    )
    content_view = target_sat.api.ContentView(id=content_view.id).read()
    # Get last two versions by id to compare
    cvv_ids = sorted(cvv.id for cvv in content_view.version)[-2:]
    result = target_sat.api.Errata().compare(
        data={'content_view_version_ids': [cvv_id for cvv_id in cvv_ids], 'per_page': '9999'}
    )
    cvv2_only_errata = next(
        errata for errata in result['results'] if errata['errata_id'] == CUSTOM_REPO_ERRATA_ID
    )
    assert cvv_ids[-1] in cvv2_only_errata['comparison']
    both_cvvs_errata = next(
        errata for errata in result['results'] if errata['errata_id'] in FAKE_9_YUM_SECURITY_ERRATUM
    )
    assert {cvv_id for cvv_id in cvv_ids} == set(both_cvvs_errata['comparison'])


@pytest.mark.tier3
def test_positive_incremental_update_required(
    module_sca_manifest_org,
    module_lce,
    activation_key,
    module_cv,
    rh_repo_module_manifest,
    rhel8_contenthost,
    target_sat,
):
    """Given a set of hosts and errata, check for content view version
    and environments that need updating."

    :id: 6dede920-ba6b-4c51-b782-c6db6ea3ee4f

    :Setup:
        1. Errata synced on satellite server

    :Steps:
        1. Create VM as Content Host, registering to CV with custom errata
        2. Install package in VM so it needs one erratum
        3. Check if incremental_updates required:
            POST /api/hosts/bulk/available_incremental_updates
        4. Assert empty [] result (no incremental update required)
        5. Apply a filter to the CV so errata will be applicable but not installable
        6. Publish the new version
        7. Promote the new version into the same LCE
        8. Check if incremental_updates required:
            POST /api/hosts/bulk/available_incremental_updates
        9. Assert incremental update is suggested


    :expectedresults: Incremental update requirement is detected.

    :parametrized: yes

    :BZ: 2013093
    """
    org = module_sca_manifest_org
    rh_repo = target_sat.api.Repository(
        id=rh_repo_module_manifest.id,
    ).read()
    rh_repo.sync()
    # Add RH repo to content-view
    target_sat.cli.ContentView.add_repository(
        {'id': module_cv.id, 'organization-id': org.id, 'repository-id': rh_repo.id}
    )
    module_cv = target_sat.api.ContentView(id=module_cv.id).read()
    _cv = cv_publish_promote(target_sat, org, module_cv, module_lce)
    module_cv = _cv['content-view']

    result = rhel8_contenthost.register(
        org=org,
        activation_keys=activation_key.name,
        target=target_sat,
        loc=None,
    )
    assert result.status == 0, f'Failed to register the host: {rhel8_contenthost.hostname}'
    assert rhel8_contenthost.subscribed
    rhel8_contenthost.execute(r'subscription-manager repos --enable \*')
    host = rhel8_contenthost.nailgun_host.read()
    # install package to create demand for an Erratum
    result = rhel8_contenthost.run(f'yum install -y {REAL_RHEL8_1_PACKAGE_FILENAME}')
    assert result.status == 0, f'Failed to install package: {REAL_RHEL8_1_PACKAGE_FILENAME}'
    # Call nailgun to make the API POST to see if any incremental updates are required
    response = target_sat.api.Host().bulk_available_incremental_updates(
        data={
            'organization_id': org.id,
            'included': {'ids': [host.id]},
            'errata_ids': [REAL_RHEL8_1_ERRATA_ID],
        },
    )
    assert not response, 'Incremental update should not be required at this point'
    # Add filter of type include but do not include anything
    # this will hide all RPMs from selected erratum before publishing
    target_sat.api.RPMContentViewFilter(
        content_view=module_cv, inclusion=True, name='Include Nothing'
    ).create()
    module_cv = target_sat.api.ContentView(id=module_cv.id).read()
    module_cv = cv_publish_promote(target_sat, org, module_cv, module_lce)['content-view']
    rhel8_contenthost.execute('subscription-manager repos')
    # Call nailgun to make the API POST to ensure an incremental update is required
    response = target_sat.api.Host().bulk_available_incremental_updates(
        data={
            'organization_id': org.id,
            'included': {'ids': [host.id]},
            'errata_ids': [REAL_RHEL8_1_ERRATA_ID],
        },
    )
    assert response, 'Nailgun response for host(s) with avaliable incremental update was None'
    assert 'next_version' in response[0], 'Incremental update should be suggested at this point'


def _run_remote_command_on_content_host(command, vm, return_result=False):
    result = vm.run(command)
    assert result.status == 0
    if return_result:
        return result.stdout
    return None


def _set_prerequisites_for_swid_repos(vm):
    _run_remote_command_on_content_host(
        f'curl --insecure --remote-name {settings.repos.swid_tools_repo}', vm
    )
    _run_remote_command_on_content_host('mv *swid*.repo /etc/yum.repos.d', vm)
    _run_remote_command_on_content_host('yum install -y swid-tools', vm)
    _run_remote_command_on_content_host('yum install -y dnf-plugin-swidtags', vm)


def _validate_swid_tags_installed(vm, module_name):
    result = _run_remote_command_on_content_host(
        f"swidq -i -n {module_name} | grep 'Name'", vm, return_result=True
    )
    assert module_name in result


@pytest.fixture
def errata_host_lce(module_sca_manifest_org, target_sat):
    """Create and return a new lce in module SCA org."""
    return target_sat.api.LifecycleEnvironment(organization=module_sca_manifest_org).create()


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
def test_errata_installation_with_swidtags(
    module_sca_manifest_org,
    rhel_contenthost,
    errata_host_lce,
    target_sat,
):
    """Verify errata installation with swid_tags and swid tags get updated after
    module stream update.

    :id: 43a59b9a-eb9b-4174-8b8e-73d923b1e51e

    :setup:

        1. rhel8 contenthost checked out, using org with simple content access.
        2. create satellite repositories having rhel8 baseOS, prereqs, custom content w/ swid tags.
        3. associate repositories to org, lifecycle environment, and cv. Sync all content.
        4. publish & promote to environment, content view version with all content.
        5. create activation key, for registering host to cv.

    :steps:

        1. register host using cv's activation key, assert succeeded.
        2. install swid-tools, dnf-plugin-swidtags packages on content host.
        3. install older module stream and generate errata, swid tag.
        4. assert errata count, swid tags are generated.
        5. install errata via updating module stream.
        6. assert errata count and swid tag changed after module update.

    :expectedresults:
        swid tags should get updated after errata installation via module stream update

    :CaseAutomation: Automated

    :parametrized: yes

    :CaseImportance: Critical

    """
    module_name = 'kangaroo'
    version = '20180704111719'
    org = module_sca_manifest_org
    lce = errata_host_lce
    cv = target_sat.api.ContentView(
        organization=org,
        environment=[lce],
    ).create()

    repos = {
        'base_os': settings.repos.rhel8_os.baseos,  # base rhel8
        'sat_tools': settings.repos.rhel8_os.appstream,  # swid prereqs
        'swid_tags': settings.repos.swid_tag.url,  # module stream pkgs and errata
    }
    # associate repos with sat, org, lce, cv, and sync
    for r in repos:
        target_sat.cli_factory.setup_org_for_a_custom_repo(
            {
                'url': repos[r],
                'organization-id': org.id,
                'lifecycle-environment-id': lce.id,
                'content-view-id': cv.id,
            },
        )
    # promote newest cv version with all repos/content
    cv = cv_publish_promote(
        sat=target_sat,
        org=org,
        cv=cv,
        lce=lce,
    )['content-view']
    # ak in env, tied to content-view
    ak = target_sat.api.ActivationKey(
        organization=org,
        environment=lce,
        content_view=cv,
    ).create()
    # register host with ak, succeeds
    result = rhel_contenthost.register(
        activation_keys=ak.name,
        target=target_sat,
        org=org,
        loc=None,
    )
    assert result.status == 0, f'Failed to register the host {target_sat.hostname},\n{result}'
    assert (
        rhel_contenthost.subscribed
    ), f'Failed to subscribe the host {target_sat.hostname}, to content.'
    result = rhel_contenthost.execute(r'subscription-manager repos --enable \*')
    assert result.status == 0, f'Failed to enable repositories with subscription-manager,\n{result}'

    # install outdated module stream package
    _set_prerequisites_for_swid_repos(rhel_contenthost)
    result = rhel_contenthost.execute(f'dnf -y module install {module_name}:0:{version}')
    assert (
        result.status == 0
    ), f'Failed to install module stream package: {module_name}:0:{version}.\n{result.stdout}'
    # recalculate errata after install of old module stream
    rhel_contenthost.execute('subscription-manager repos')

    # validate swid tags Installed
    result = rhel_contenthost.execute(
        f'swidq -i -n {module_name} | grep "File" | grep -o "rpm-.*.swidtag"',
    )
    assert (
        result.status == 0
    ), f'An error occured trying to fetch swid tags for {module_name}.\n{result}'
    before_errata_apply_result = result.stdout
    assert before_errata_apply_result != '', f'Found no swid tags contained in {module_name}.'
    assert (app_errata_count := rhel_contenthost.applicable_errata_count) == 1, (
        f'Found {rhel_contenthost.applicable_errata_count} applicable errata,'
        f' after installing {module_name}:0:{version}, expected 1.'
    )

    # apply modular errata
    result = rhel_contenthost.execute(f'dnf -y module update {module_name}')
    assert (
        result.status == 0
    ), f'Failed to update module stream package: {module_name}.\n{result.stdout}'
    assert rhel_contenthost.execute('dnf -y upload-profile').status == 0

    # recalculate and check errata after modular update
    rhel_contenthost.execute('subscription-manager repos')
    app_errata_count -= 1
    assert rhel_contenthost.applicable_errata_count == app_errata_count, (
        f'Found {rhel_contenthost.applicable_errata_count} applicable errata, after modular update of {module_name},'
        f' expected {app_errata_count}.'
    )
    # swidtags were updated based on package version
    result = rhel_contenthost.execute(
        f'swidq -i -n {module_name} | grep "File" | grep -o "rpm-.*.swidtag"',
    )
    assert (
        result.status == 0
    ), f'An error occured trying to fetch swid tags for {module_name}.\n{result}'
    after_errata_apply_result = result.stdout
    assert before_errata_apply_result != after_errata_apply_result


@pytest.fixture(scope='module')
def rh_repo_module_manifest(module_sca_manifest_org, module_target_sat):
    """Use module manifest org, creates tools repo, syncs and returns RH repo."""
    # enable rhel repo and return its ID
    rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_sca_manifest_org.id,
        product=PRDS['rhel8'],
        repo=REPOS['rhst8']['name'],
        reposet=REPOSET['rhst8'],
        releasever='None',
    )
    # Sync step because repo is not synced by default
    rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


@pytest.mark.tier3
def test_positive_incremental_update_apply_to_envs_cvs(
    target_sat,
    module_sca_manifest_org,
    rhel8_contenthost,
    module_product,
):
    """With multiple environments and content views, register a host to one,
        apply a CV filter to the content-view, and query available incremental update(s).

        Then, execute the available update with security errata, inspect the environment(s) and
        content-view with the new incremental version. Check the errata and packages available on host.

    :id: ce8bd9ed-8fbc-40f2-8e58-e9b520fe94a3

    :Setup:
        1. Security Errata synced on satellite server from custom repo.
        2. Multiple content-views promoted to multiple environments.
        3. Register a RHEL host to the content-view with activation key.
        4. Install outdated packages, some applicable to the erratum and some not.

    :Steps:
        1. Add an inclusive Erratum filter to the host content-view
        2. POST /api/hosts/bulk/available_incremental_updates
        3. POST /katello/api/content_view_versions/incremental_update

    :expectedresults:
        1. Incremental update is available to expected content-view in
            expected environment(s), applicable to expected host.
        2. A new content-view incremental version is created and promoted,
            the applicable errata are then available to the host.
        3. We can install packages and see updated applicable errata within the
            incremental version of the content-view.

    """
    # any existing custom CVs in org, except Default CV
    prior_cv_count = (
        len(target_sat.api.ContentView(organization=module_sca_manifest_org).search()) - 1
    )
    # Number to be Created: new LCE's for org, new CV's per LCE.
    number_of_lces = 3  # Does not include 'Library'
    number_of_cvs = 3  # Does not include 'Default Content View'
    lce_library = _fetch_library_environment_for_org(target_sat, module_sca_manifest_org)
    lce_list = [lce_library]
    # custom repo with errata
    custom_repo = target_sat.api.Repository(
        product=module_product, content_type='yum', url=CUSTOM_REPO_URL
    ).create()
    custom_repo.sync()

    # create multiple linked environments
    for n in range(number_of_lces):
        new_lce = target_sat.api.LifecycleEnvironment(
            organization=module_sca_manifest_org,
            prior=lce_list[n],
        ).create()
        lce_list.append(new_lce)
    assert len(lce_list) == number_of_lces + 1
    # collect default CV for org
    default_cv = (
        target_sat.api.ContentView(
            organization=module_sca_manifest_org,
            name=DEFAULT_CV,
        )
        .search()[0]
        .read()
    )
    cv_list = list([default_cv])
    # for each environment including 'Library'
    for _lce in lce_list:
        # create some new CVs with some content
        for _i in range(number_of_cvs):
            new_cv = target_sat.api.ContentView(
                organization=module_sca_manifest_org,
                repository=[custom_repo],
            ).create()
            # lces to be promoted to, omit newer than _lce in loop
            env_ids = sorted([lce.id for lce in lce_list if lce.id <= _lce.id])
            # when the only lce to publish to is Library, pass None to default
            if len(env_ids) == 1 and env_ids[0] == lce_library.id:
                env_ids = None
            # we may initially promote out of order, use force to bypass
            new_cv = cv_publish_promote(
                target_sat,
                module_sca_manifest_org,
                new_cv,
                lce=env_ids,
                force=True,
            )['content-view']
            cv_list.append(new_cv)

    # total amount of CVs created matches expected and search results
    assert len(cv_list) == 1 + (number_of_cvs * (number_of_lces + 1))
    assert prior_cv_count + len(cv_list) == len(
        target_sat.api.ContentView(organization=module_sca_manifest_org).search()
    )
    # one ak with newest CV and lce
    host_lce = lce_list[-1].read()
    host_cv = cv_list[-1].read()
    ak = target_sat.api.ActivationKey(
        organization=module_sca_manifest_org,
        environment=host_lce,
        content_view=host_cv,
    ).create()
    # content host, global registration
    result = rhel8_contenthost.register(
        org=module_sca_manifest_org,
        activation_keys=ak.name,
        target=target_sat,
        loc=None,
    )
    assert result.status == 0, f'Failed to register the host: {rhel8_contenthost.hostname}'
    assert rhel8_contenthost.subscribed
    rhel8_contenthost.execute(r'subscription-manager repos --enable \*')
    # Installing all outdated packages
    pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
    assert rhel8_contenthost.execute(f'yum install -y {pkgs}').status == 0
    rhel8_contenthost.execute('subscription-manager repos')
    # After installing packages, check available incremental updates
    host = rhel8_contenthost.nailgun_host.read()
    response = target_sat.api.Host().bulk_available_incremental_updates(
        data={
            'organization_id': module_sca_manifest_org.id,
            'included': {'ids': [host.id]},
            'errata_ids': FAKE_9_YUM_SECURITY_ERRATUM,
        },
    )
    # expecting no available updates before CV change
    assert (
        response == []
    ), f'No incremental updates should currently be available to host: {rhel8_contenthost.hostname}.'

    # New Erratum CV filter created for host view
    target_sat.api.ErratumContentViewFilter(content_view=host_cv, inclusion=True).create()
    host_cv = target_sat.api.ContentView(id=host_cv.id).read()
    lce_ids = sorted([lce.id for lce in lce_list])
    # publish version with filter and promote
    host_cvv = cv_publish_promote(
        target_sat,
        module_sca_manifest_org,
        host_cv,
        lce_ids,
    )['content-view-version']

    # cv is not updated to host yet, applicable errata should be zero
    rhel8_contenthost.execute('subscription-manager repos')
    host_app_errata = rhel8_contenthost.applicable_errata_count
    assert host_app_errata == 0
    # After adding filter to cv, check available incremental updates
    host_app_packages = rhel8_contenthost.applicable_package_count
    response = target_sat.api.Host().bulk_available_incremental_updates(
        data={
            'organization_id': module_sca_manifest_org.id,
            'included': {'ids': [host.id]},
            'errata_ids': FAKE_9_YUM_SECURITY_ERRATUM,
        },
    )
    assert (
        response
    ), f'Expected one incremental update, but found none, for host: {rhel8_contenthost.hostname}.'
    # find that only expected CV version has incremental update available
    assert (
        len(response) == 1
    ), f'Incremental update should currently be available to only one host: {rhel8_contenthost.hostname}.'
    next_version = float(response[0]['next_version'])
    assert float(host_cvv.version) + 0.1 == next_version  # example: 2.0 > 2.1
    assert response[0]['content_view_version']['id'] == host_cvv.id
    assert response[0]['content_view_version']['content_view']['id'] == host_cv.id

    # Perform Incremental Update with host cv version
    host_cvv = target_sat.api.ContentViewVersion(id=host_cvv.id).read()
    # Apply incremental update adding the applicable security erratum
    response = target_sat.api.ContentViewVersion().incremental_update(
        data={
            'content_view_version_environments': [
                {
                    'content_view_version_id': host_cvv.id,
                    'environment_ids': [host_lce.id],
                }
            ],
            'add_content': {'errata_ids': FAKE_9_YUM_SECURITY_ERRATUM},
        }
    )
    assert response['result'] == 'success'
    assert (
        response['action']
        == 'Incremental Update of 1 Content View Version(s) with 12 Package(s), and 3 Errata'
    )

    # only the hosts's CV was modified, new version made, check output details
    assert len(response['output']['changed_content']) == 1
    created_version_id = response['output']['changed_content'][0]['content_view_version']['id']
    # host source CV version was changed to the new one
    host_version_id = host.read().get_values()['content_facet_attributes'][
        'content_view_version_id'
    ]
    assert host_version_id == created_version_id
    # get newest version by highest id
    version_ids = sorted([ver.id for ver in host_cv.read().version])
    assert created_version_id == version_ids[-1]
    # latest sat and host version matches incremental one
    host_version_number = float(
        host.read().get_values()['content_facet_attributes']['content_view_version']
    )
    assert host_version_number == next_version
    host_cvv = target_sat.api.ContentViewVersion(id=created_version_id).read()
    assert float(host_cvv.version) == next_version
    rhel8_contenthost.execute('subscription-manager repos')
    # expected errata from FAKE_9 Security list added
    added_errata = response['output']['changed_content'][0]['added_units']['erratum']
    assert set(added_errata) == set(FAKE_9_YUM_SECURITY_ERRATUM)
    # applicable errata count increased by length of security ids list
    assert rhel8_contenthost.applicable_errata_count == host_app_errata + len(
        FAKE_9_YUM_SECURITY_ERRATUM
    )
    # newly added errata from incremental version are now applicable to host
    post_app_errata_ids = errata_id_set(
        _fetch_available_errata_instances(target_sat, rhel8_contenthost)
    )
    assert set(FAKE_9_YUM_SECURITY_ERRATUM).issubset(post_app_errata_ids)
    # expected packages from the security erratum were added to host
    added_packages = response['output']['changed_content'][0]['added_units']['rpm']
    assert len(added_packages) == 12
    # expected that not all of the added packages will be applicable
    assert 8 == host_app_packages == rhel8_contenthost.applicable_package_count
    # install all of the newly added packages, recalculate applicability
    for pkg in added_packages:
        assert rhel8_contenthost.run(f'yum install -y {pkg}').status == 0
    rhel8_contenthost.execute('subscription-manager repos')
    # security errata should not be applicable after installing updated packages
    post_app_errata_ids = errata_id_set(
        _fetch_available_errata_instances(target_sat, rhel8_contenthost)
    )
    assert set(FAKE_9_YUM_SECURITY_ERRATUM).isdisjoint(post_app_errata_ids)
    assert rhel8_contenthost.applicable_errata_count == 0

    # after applying the incremental update, check for any more available
    response = target_sat.api.Host().bulk_available_incremental_updates(
        data={
            'organization_id': module_sca_manifest_org.id,
            'included': {'ids': [host.id]},
            'errata_ids': FAKE_9_YUM_SECURITY_ERRATUM,
        },
    )
    # expect no remaining updates, after applying the only one
    assert (
        response == []
    ), f'No incremental updates should currently be available to host: {rhel8_contenthost.hostname}.'
