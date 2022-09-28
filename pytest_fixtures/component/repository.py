# Repository Fixtures
import pytest
from fauxfactory import gen_string
from nailgun import entities
from nailgun.entity_mixins import call_entity_method_with_timeout

from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


@pytest.fixture(scope='function')
def function_product(function_org):
    return entities.Product(organization=function_org).create()


@pytest.fixture(scope='module')
def module_product(module_org, module_target_sat):
    return module_target_sat.api.Product(organization=module_org).create()


@pytest.fixture(scope='module')
def rh_repo_gt_manifest(module_gt_manifest_org):
    """Use GT manifest org, creates RH tools repo, syncs and returns RH repo."""
    # enable rhel repo and return its ID
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_gt_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    # Sync step because repo is not synced by default
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


@pytest.fixture(scope='module')
def module_rhst_repo(module_target_sat, module_org_with_manifest, module_promoted_cv, module_lce):
    """Use module org with manifest, creates RH tools repo, syncs and returns RH repo id."""
    # enable rhel repo and return its ID
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_org_with_manifest.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    cv = module_target_sat.api.ContentView(id=module_promoted_cv.id, repository=[rh_repo]).update(
        ["repository"]
    )
    cv.publish()
    cv = cv.read()
    cv.version[-1].promote(data={'environment_ids': module_lce.id})
    return REPOS['rhst7']['id']


@pytest.fixture(scope="function")
def repo_setup():
    """
    This fixture is used to create an organization, product, repository, and lifecycle environment
    and once the test case gets completed then it performs the teardown of that.
    """
    repo_name = gen_string('alpha')
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    repo = entities.Repository(name=repo_name, product=product).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    details = {'org': org, 'product': product, 'repo': repo, 'lce': lce}
    yield details


@pytest.fixture(scope='module')
def module_repository(os_path, module_product, module_target_sat):
    repo = module_target_sat.api.Repository(product=module_product, url=os_path).create()
    call_entity_method_with_timeout(module_target_sat.api.Repository(id=repo.id).sync, timeout=3600)
    return repo


def _simplify_repos(request, repos):
    """This is a helper function that transforms repos_collection related fixture parameters into
    a list that can be passed to robottelo.host_helpers.RepositoryMixins.RepositoryCollection
    class constructor arguments. It can create multiple repos with distro.

    E.g: the parameters list to repos_collection fixture is:
    [{
        'distro': 'rhel7',
        'SatelliteToolsRepository': {},
        'YumRepository': [{'url': settings.repos.yum_0.url},{'url': settings.repos.yum_6.url}]
    }]

    The fixture removes distro from the dict above and translates the remaining dictionary into
    [
        {'SatelliteToolsRepository': {}},
        {'YumRepository': {'url': settings.repos.yum_0.url}},
        {'YumRepository': {'url': settings.repos.yum_6.url}}
    ]
    Then the fixtures loop over it to create multiple repositories.

    :returns: The tuple of distro of repositories(if given) and simplified repos
    """
    _repos = []
    repo_distro = None
    # Iterating over repository thats requested more than once
    for repo_name, repo_options in repos.items():
        if isinstance(repo_options, list):
            [_repos.append({repo_name: options}) for options in repo_options]
        else:
            _repos.append({repo_name: repo_options})
    # Fetching repo collection distro from the parameters separately
    _repo_distro = list(filter(lambda _params: 'distro' in _params, _repos))
    if _repo_distro:
        repo_distro = _repos.pop(_repos.index(_repo_distro[0]))['distro']
    # Use CDN and distro param values from its own param on test if
    # not provided in repo_collection params
    for index, repo in enumerate(_repos):
        (repo_name, repo_params), *_ = repo.items()
        for option in ['cdn', 'distro']:
            if option in repo_params:
                param_value = _repos[index][repo_name][option]
                _repos[index][repo_name][option] = (
                    request.getfixturevalue(option) if param_value == option else param_value
                )
    return repo_distro, _repos


@pytest.fixture
def repos_collection(request, target_sat):
    """Use this fixture with parameters, in tests and fixtures, that needs to create multiple repos
    and operate on bunch of those repositories using robottelo.host_helpers.RepositoryMixins repo
    helper classes.

    Remember:
        1. This fixture uses CLI Endpoint to create repository collection.
        2. The only parameter to this fixture should be a list of dicts of Repositories
        with repo parameters.
        3. To add distro to the repository(ies), You can either pass distro param in repository
        dict in params list directly -OR- add distro key value to repos_collection repos and
        its params list -OR- add distro pytest mark with multiple distros list.

    Check various types of usage in following tests:
        1. tests.foreman.ui.test_activationkey.test_positive_end_to_end_register
            Where the distro param is added as a key value to a specific repository dict applies
            to only that repository
        2. tests.foreman.ui.test_contentview.test_positive_remove_cv_version_from_env
            Where the distro key value is added with the list of repositories dicts applies to all
            the repos in the list
        3. tests.foreman.cli.test_vm_install_products_packages.test_vm_install_package
            Where the cdn and distro are pytest marks and repos collection fixture uses values from
            those marks to generate multitests based on distro and cdn combinations. To capture the
            value of cdn / distro from pytest params in specific repo one has to add
            `cdn` / 'distro' as value to cdn / distro arguments

    """
    repos = getattr(request, 'param', [])
    repo_distro, repos = _simplify_repos(request, repos)
    _repos_collection = target_sat.cli_factory.RepositoryCollection(
        distro=repo_distro or request.getfixturevalue('distro'),
        repositories=[
            getattr(target_sat.cli_factory, repo_name)(**repo_params)
            for repo in repos
            for repo_name, repo_params in repo.items()
        ],
    )
    return _repos_collection


@pytest.fixture(scope='module')
def module_repos_collection_with_setup(request, module_target_sat, module_org, module_lce):
    """This fixture and its usage is very similar to repos_collection fixture above with extra
    setup_content capabilities using module_org and module_lce fixtures

    Remember:
        1. One can not pass distro as pytest mark via test to this fixture since the conflict of
        using function scoped distro fixture in module scoped this fixture arrives

    """
    repos = getattr(request, 'param', [])
    repo_distro, repos = _simplify_repos(request, repos)
    _repos_collection = module_target_sat.cli_factory.RepositoryCollection(
        distro=repo_distro,
        repositories=[
            getattr(module_target_sat.cli_factory, repo_name)(**repo_params)
            for repo in repos
            for repo_name, repo_params in repo.items()
        ],
    )
    _repos_collection.setup_content(module_org.id, module_lce.id)
    return _repos_collection


@pytest.fixture(scope='module')
def module_repos_collection_with_manifest(request, module_target_sat, module_org, module_lce):
    """This fixture and its usage is very similar to repos_collection fixture above with extra
    setup_content and uploaded manifest capabilities using module_org and module_lce fixtures

    Remember:
        1. One can not pass distro as pytest mark via test to this fixture since the conflict of
        using function scoped distro fixture in module scoped this fixture arrives
    """
    repos = getattr(request, 'param', [])
    repo_distro, repos = _simplify_repos(request, repos)
    _repos_collection = module_target_sat.cli_factory.RepositoryCollection(
        distro=repo_distro,
        repositories=[
            getattr(module_target_sat.cli_factory, repo_name)(**repo_params)
            for repo in repos
            for repo_name, repo_params in repo.items()
        ],
    )
    _repos_collection.setup_content(module_org.id, module_lce.id, upload_manifest=True)
    return _repos_collection
