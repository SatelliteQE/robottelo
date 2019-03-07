# -*- encoding: utf-8 -*-
"""Manage RH products repositories and custom repositories.

The main purpose of this feature is to manage product repositories especially
the RH one in the context of a special distro and cdn settings.

The repository data creation became transparent when supplying only the target
distro.

Example Usage:

We know that sat tool key = 'rhst'

Working with generic repos.

Generic repos has no way to guess the custom repo url in case of
settings.cdn = false , that why the GenericRHRepo without custom url always
return cdn repo data:

    sat_repo = GenericRHRepository(key=PRODUCT_KEY_SAT_TOOLS)
    print(sat_repo.cdn) >> True
    # today the default distro is rhel7
    print(sat_repo.distro)  >> rhel7
    print(sat_repo.data) >>
    {
    'arch': 'x86_64',
    'cdn': True,
    'product': 'Red Hat Enterprise Linux Server',
    'releasever': None,
    'repository': 'Red Hat Satellite Tools 6.2 for RHEL 7 Server RPMs x86_64',
    'repository-id': 'rhel-7-server-satellite-tools-6.2-rpms',
    'repository-set': 'Red Hat Satellite Tools 6.2 (for RHEL 7 Server) (RPMs)'
    }

    # Generic CDN RH repository with specific distro "DISTRO_RHEL6"
    sat_repo = GenericRHRepository(
        distro=DISTRO_RHEL6, key=PRODUCT_KEY_SAT_TOOLS)

    print(sat_repo.distro) >> rhel6
    print(sat_repo.data)   >>
    {
    'arch': 'x86_64',
    'cdn': True,
    'product': 'Red Hat Enterprise Linux Server',
    'releasever': None,
    'repository': 'Red Hat Satellite Tools 6.2 for RHEL 6 Server RPMs x86_64',
    'repository-id': 'rhel-6-server-satellite-tools-6.2-rpms',
    'repository-set': 'Red Hat Satellite Tools 6.2 (for RHEL 6 Server) (RPMs)'
    }

    # Generic RH repository with custom url
    sat_repo = GenericRHRepository(
        key=PRODUCT_KEY_SAT_TOOLS, url='http://sat-tools.example.com')

    # because default settings.cdn=False and we have a custom url
    print(sat_repo.cdn) >> False
    print(sat_repo.distro) >> rhel7
    print(sat_repo.data) >>
    {'cdn': False, 'url': 'http://sat-tools.example.com'}

    # Generic RH repository with custom url and force cdn
    sat_repo = GenericRHRepository(
        key=PRODUCT_KEY_SAT_TOOLS,
        url='http://sat-tools.example.com',
        cdn=True
    )
    print(sat_repo.data) >>
    {
    'arch': 'x86_64',
    'cdn': True,
    'product': 'Red Hat Enterprise Linux Server',
    'releasever': None,
    'repository': 'Red Hat Satellite Tools 6.2 for RHEL 7 Server RPMs x86_64',
    'repository-id': 'rhel-7-server-satellite-tools-6.2-rpms',
    'repository-set': 'Red Hat Satellite Tools 6.2 (for RHEL 7 Server) (RPMs)'
    }

    # We have created a SatelliteToolsRepository that automatically detect it's
    # custom url in settings, so there no need to explicitly initialise with
    # url, simply the distro is needed (in case of specific one), otherwise
    # the default distro will be used.

    # SatelliteToolsRepository RH repo use settings urls and cdn
    sat_repo = SatelliteToolsRepository()
    print(sat_repo.cdn) >> False
    print(sat_repo.distro) >> rhel7
    print(sat_repo.data) >>
    {
    'cdn': False,
    # part of the url was hidden
    'url': 'XXXXXXXXXXXXXXXXXXX/Tools_6_3_RHEL7/custom/'
           'Satellite_Tools_6_3_Composes/Satellite_Tools_x86_64/'
    }

    # SatelliteToolsRepository RH repo use settings urls with 'force cdn')
    sat_repo = SatelliteToolsRepository(cdn=True)
    print(sat_repo.cdn >> True
    print(sat_repo.distro >> rhel7
    print(sat_repo.data >>
    {
    'arch': 'x86_64',
    'cdn': True,
    'product': 'Red Hat Enterprise Linux Server',
    'releasever': None,
    'repository': 'Red Hat Satellite Tools 6.2 for RHEL 7 Server RPMs x86_64',
    'repository-id': 'rhel-7-server-satellite-tools-6.2-rpms',
    'repository-set': 'Red Hat Satellite Tools 6.2 (for RHEL 7 Server) (RPMs)'
    }

    # we can also indicate the distro, the same as for the generic one the
    # data will be switched for that distro


    # Working with RepositoryCollection using the default distro
    repos_collection = RepositoryCollection(
        repositories=[
            RHELRepository(),
            SatelliteToolsRepository(),
            SatelliteCapsuleRepository(),
            CustomYumRepository(url=FAKE_0_YUM_REPO)
        ]
    )

    repos_collection.distro >> None
    repos_collection.repos_data >>
    [{'cdn': False,
      'url': 'http://XXXXXXXXX/RHEL-7/7.4/Server/x86_64/os/'},
     {'cdn': False,
      'url': 'http://XXXXXXXXXXX/Tools_6_3_RHEL7/custom/'
             'Satellite_Tools_6_3_Composes/Satellite_Tools_x86_64/'
             },
     {'cdn': False,
      'url': 'http://XXXXXXXXXX/Satellite_6_3_RHEL7/custom/'
             'Satellite_6_3_Composes/Satellite_6_3_RHEL7'
             },
     {'cdn': False, 'url': 'http://inecas.fedorapeople.org/fakerepos/zoo/'}
    ]
    repos_collection.need_subscription >> False

    # Working with RepositoryCollection with force distro RHEL6 and force cdn
    # on some repos
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL6,
        repositories=[
            SatelliteToolsRepository(cdn=True),
            SatelliteCapsuleRepository(),
            YumRepository(url=FAKE_0_YUM_REPO)
        ]
    )
    repos_collection.distro >> rhel6
    repos_collection.repos_data >>
    [
        {'arch': 'x86_64',
         'cdn': True,
         'product': 'Red Hat Enterprise Linux Server',
         'releasever': None,
         'repository': 'Red Hat Satellite Tools 6.2 for RHEL 6 Server RPMs'
                       ' x86_64',
         'repository-id': 'rhel-6-server-satellite-tools-6.2-rpms',
         'repository-set': 'Red Hat Satellite Tools 6.2 (for RHEL 6 Server)
                           '(RPMs)'
        },
        {
        'arch': 'x86_64',
        'cdn': True,
        'product': 'Red Hat Satellite Capsule',
        'releasever': None,
        'repository': 'Red Hat Satellite Capsule 6.2 for RHEL 6 Server RPMs '
                      'x86_64',
        'repository-id': 'rhel-6-server-satellite-capsule-6.2-rpms',
        'repository-set': 'Red Hat Satellite Capsule 6.2 (for RHEL 6 Server) '
                          '(RPMs)'
        },
        {'cdn': False, 'url': 'http://inecas.fedorapeople.org/fakerepos/zoo/'}
    ]
    repos_collection.need_subscription >> True
    # Note: satellite capsule repo will query the server for a distro and if
    # the same distro as the sat server is used will use the settings url
    # (if cdn=False) else it will use the cdn one.

    # Please consult the RepositoryCollection for some usage functions
    # also test usage located at:
    # tests/foreman/cli/test_vm_install_products_package.py
"""
from typing import Any, Dict, List, Tuple, Optional, TYPE_CHECKING  # noqa

from robottelo.cli.factory import (
    make_activation_key,
    make_content_view,
    make_product_wait,
    make_repository,
    setup_virtual_machine,
)
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.org import Org
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_SUBSCRIPTION_NAME,
    DISTRO_DEFAULT,
    DISTRO_RHEL6,
    DISTROS_MAJOR_VERSION,
    DISTROS_SUPPORTED,
    ENVIRONMENT,
    MAJOR_VERSION_DISTRO,
    REPO_TYPE,
    REPOS,
)
from robottelo.decorators import bz_bug_is_open
from robottelo.helpers import get_host_info
from robottelo import manifests
if TYPE_CHECKING:
    from robottelo.vm import VirtualMachine  # noqa

REPO_TYPE_YUM = REPO_TYPE['yum']
REPO_TYPE_DOCKER = REPO_TYPE['docker']
REPO_TYPE_PUPPET = REPO_TYPE['puppet']
REPO_TYPE_OSTREE = REPO_TYPE['ostree']

DOWNLOAD_POLICY_ON_DEMAND = 'on_demand'
DOWNLOAD_POLICY_IMMEDIATE = 'immediate'
DOWNLOAD_POLICY_BACKGROUND = 'background'

PRODUCT_KEY_RHEL = 'rhel'
PRODUCT_KEY_SAT_TOOLS = 'rhst'
PRODUCT_KEY_SAT_CAPSULE = 'rhsc'
PRODUCT_KEY_VIRT_AGENTS = 'rhva6'
PRODUCT_KEY_CLOUD_FORMS_TOOLS = 'rhct6'
PRODUCT_KEY_ANSIBLE_ENGINE = 'rhae2'

_server_distro = None  # type: str


class RepositoryAlreadyDefinedError(Exception):
    """Raised when a repository has already a predefined key"""


class DistroNotSupportedError(Exception):
    """Raised when using a non supported distro"""


class RepositoryDataNotFound(Exception):
    """Raised when repository data cannot be found for a predefined distro"""


class OnlyOneOSRepositoryAllowed(Exception):
    """Raised when trying to more than one OS repository to a collection"""


class RepositoryAlreadyCreated(Exception):
    """Raised when a repository content is already created and trying to launch
    the create an other time"""


class ReposContentSetupWasNotPerformed(Exception):
    """Raised when trying to setup a VM but the repositories content was not
    setup"""


def get_server_distro():  # type: () -> str
    global _server_distro
    if _server_distro is None:
        _, major, _ = get_host_info()
        _server_distro = MAJOR_VERSION_DISTRO[major]
    return _server_distro


class BaseRepository(object):
    """Base repository class for custom and RH repositories"""
    _url = None  # type: Optional[str]
    _distro = None  # type: Optional[str]
    _type = None  # type: Optional[str]
    _repo_info = None  # type: Optional[Dict]

    def __init__(self, url=None, distro=None, content_type=None):
        self._url = url
        self.distro = distro
        if content_type is not None:
            self._type = content_type

    @property
    def url(self):  # type: () -> Optional[str]
        return self._url

    @property
    def cdn(self):  # type: () -> bool
        return False

    @property
    def data(self):  # type: () -> Dict
        data = dict(url=self.url, cdn=self.cdn)
        content_type = self.content_type
        if content_type:
            data['content-type'] = content_type
        return data

    @property
    def distro(self):  # type: () -> Optional[str]
        """Return the current distro"""
        return self._distro

    @distro.setter
    def distro(self, value):
        """Set the distro"""
        self._distro = value

    @property
    def content_type(self):   # type: () -> str
        return self._type

    def __repr__(self):
        return '<Repo type: {0}, url: {1}, object: {2}>'.format(
            self.content_type, self.url, hex(id(self)))

    @property
    def repo_info(self):  # type: () -> Optional[Dict]
        return self._repo_info

    def create(self, organization_id, product_id,
               download_policy=DOWNLOAD_POLICY_ON_DEMAND, synchronize=True):
        # type: (int, int, str, bool) -> Dict
        """Create the repository for the supplied product id"""
        create_options = {
            'product-id': product_id,
            'content-type': self.content_type,
            'url': self.url,
        }
        if self.content_type == REPO_TYPE_YUM and download_policy:
            create_options['download-policy'] = download_policy
        if self.content_type == REPO_TYPE_OSTREE:
            create_options['publish-via-http'] = 'false'
        repo_info = make_repository(create_options)
        self._repo_info = repo_info
        if synchronize:
            self.synchronize()
        return repo_info

    def synchronize(self):
        """Synchronize the repository"""
        Repository.synchronize({'id': self.repo_info['id']}, timeout=4800)

    def add_to_content_view(self, organization_id, content_view_id):
        # type: (int, int) -> None
        """Associate repository content to content-view"""
        ContentView.add_repository({
            'id': content_view_id,
            'organization-id': organization_id,
            'repository-id': self._repo_info['id'],
        })


class YumRepository(BaseRepository):
    """Custom Yum repository"""
    _type = REPO_TYPE_YUM  # type: str


class DockerRepository(BaseRepository):
    """Custom Docker repository"""
    _type = REPO_TYPE_DOCKER  # type: str

    def __init__(self, url=None, distro=None, upstream_name=None):
        self._upstream_name = upstream_name
        super(DockerRepository, self).__init__(url=url, distro=distro)

    @property
    def upstream_name(self):
        return self._upstream_name

    def create(self, organization_id, product_id, download_policy=None, synchronize=True):
        repo_info = make_repository({
            'product-id': product_id,
            'content-type': self.content_type,
            'url': self.url,
            'docker-upstream-name': self.upstream_name,
        })
        self._repo_info = repo_info
        if synchronize:
            self.synchronize()
        return repo_info


class PuppetRepository(BaseRepository):
    """Custom Puppet repository"""
    _type = REPO_TYPE_PUPPET  # type: str

    def __init__(self, url=None, distro=None, modules=None):
        # type: (str, Optional[str], List[Dict[str, str]]) -> None
        self._puppet_modules = modules
        super(PuppetRepository, self).__init__(url=url, distro=distro)

    @property
    def puppet_modules(self):
        return self._puppet_modules

    def add_to_content_view(self, organization_id, content_view_id):
        # type: (int, int) -> None
        """Associate repository content to content-view"""
        options = {
            'content-view-id': content_view_id,
            'organization-id': organization_id,
        }
        for puppet_module in self.puppet_modules:
            module_options = options.copy()
            module_options.update(puppet_module)
            ContentView.puppet_module_add(module_options)


class OSTreeRepository(BaseRepository):
    """Custom OSTree repository"""
    _type = REPO_TYPE_OSTREE


class GenericRHRepository(BaseRepository):
    """Generic RH repository"""
    _type = REPO_TYPE_YUM
    _distro = DISTRO_DEFAULT  # type: str
    _key = None  # type: str
    _repo_data = None  # type: Dict
    _url = None  # type: Optional[str]

    def __init__(self, distro=None, key=None, cdn=False, url=None):
        super(GenericRHRepository, self).__init__()

        if key is not None and self.key:
            raise RepositoryAlreadyDefinedError(
                'Repository key already defined')

        if key is not None:
            self._key = key

        if url is not None:
            self._url = url

        self._cdn = bool(cdn)

        self.distro = distro

    @property
    def url(self):
        return self._url

    @property
    def cdn(self):
        return bool(self._cdn or settings.cdn or not self.url)

    @property
    def key(self):
        return self._key

    @property
    def distro(self):
        return self._distro

    @distro.setter
    def distro(self, distro):  # type: (str) -> None
        """Set a new distro value, we have to reinitialise the repo data also,
        if not found raise exception
        """

        if distro is not None and distro not in DISTROS_SUPPORTED:
            raise DistroNotSupportedError(
                'distro "{0}" not supported'.format(distro))
        if distro is None:
            distro = self._distro
        repo_data = self._get_repo_data(distro)
        if repo_data is None:
            raise RepositoryDataNotFound(
                'Repository data not found for distro {}'.format(distro))
        self._distro = distro
        self._repo_data = repo_data

    def _get_repo_data(self, distro=None):  # type: (Optional[str]) -> Dict
        """Return the repo data as registered in constant module and bound
        to distro.
        """
        if distro is None:
            distro = self.distro
        repo_data = None
        for _, data in REPOS.items():
            repo_key = data.get('key')
            repo_distro = data.get('distro')
            if repo_key == self.key and repo_distro == distro:
                repo_data = data
                break
        return repo_data

    @property
    def repo_data(self):  # type: () -> Dict
        if self._repo_data is not None:
            return self._repo_data
        self._repo_data = self._get_repo_data()
        return self._repo_data

    def _repo_is_distro(self, repo_data=None):
        # type: (Optional[Dict]) -> bool
        """return whether the repo data is for an OS distro product repository"""
        if repo_data is None:
            repo_data = self.repo_data
        return bool(repo_data.get('distro_repository', False))

    @property
    def is_distro_repository(self):  # type: () -> bool
        # whether the current repository is an OS distro product repository
        return self._repo_is_distro()

    @property
    def distro_major_version(self):
        return DISTROS_MAJOR_VERSION[self.distro]

    @property
    def distro_repository(self):  # type: () -> Optional[RHELRepository]
        """Return the OS distro repository object relied to this repository

        Suppose we have a repository for a product that must be installed on
        RHEL, but for proper installation needs some dependencies packages from
        the OS repository. This function will return the right OS repository
        object for later setup.

        for example:
           capsule_repo = SatelliteCapsuleRepository()
           # the capsule_repo will represent a capsule repo for default distro
           rhel_repo = capsule_repo.distro_repository
           # the rhel repo representation object for default distro will be
           # returned, if not found raise exception
        """
        if self.is_distro_repository:
            return self
        distro_repo_data = None
        for _, repo_data in REPOS.items():
            if (repo_data.get('distro') == self.distro
                    and self._repo_is_distro(repo_data=repo_data)):
                distro_repo_data = repo_data
                break

        if distro_repo_data:
            return RHELRepository(distro=self.distro, cdn=self.cdn)
        return None

    @property
    def rh_repository_id(self):  # type: () -> Optional[str]
        if self.cdn:
            return self.repo_data.get('id')
        return None

    @property
    def data(self):  # type: () -> Dict
        data = {}
        if self.cdn:
            data['product'] = self.repo_data.get('product')
            data['repository-set'] = self.repo_data.get('reposet')
            data['repository'] = self.repo_data.get('name')
            data['repository-id'] = self.repo_data.get('id')
            data['releasever'] = self.repo_data.get('releasever')
            data['arch'] = self.repo_data.get('arch', DEFAULT_ARCHITECTURE)
            data['cdn'] = True
        else:
            data['url'] = self.url
            data['cdn'] = False

        return data

    def __repr__(self):
        if self.cdn:
            return '<RH cdn Repo: {0} within distro:{1}, object: {2}>'.format(
                self.data['repository'], self.distro, hex(id(self)))
        else:
            return '<RH custom Repo url: {0} object: {1}>'.format(
                self.url, hex(id(self)))

    def create(self, organization_id, product_id=None,
               download_policy=DOWNLOAD_POLICY_ON_DEMAND, synchronize=True):
        # type: (int, Optional[int], Optional[str], Optional[bool]) -> Dict
        """Create an RH repository"""
        if not self.cdn and not self.url:
            raise ValueError('Can not handle Custom repository with url not supplied')
        if self.cdn:
            data = self.data
            RepositorySet.enable({
                'organization-id': organization_id,
                'product': data['product'],
                'name': data['repository-set'],
                'basearch': data.get('arch', DEFAULT_ARCHITECTURE),
                'releasever': data.get('releasever'),
            })
            repo_info = Repository.info({
                'organization-id': organization_id,
                'name': data['repository'],
                'product': data['product'],
            })
            if download_policy:
                # Set download policy
                Repository.update({
                    'download-policy': download_policy,
                    'id': repo_info['id'],
                })
            self._repo_info = repo_info
            if synchronize:
                self.synchronize()
        else:
            repo_info = super(GenericRHRepository, self).create(
                organization_id, product_id, download_policy=download_policy)
        return repo_info


class RHELRepository(GenericRHRepository):
    """RHEL repository"""
    _key = PRODUCT_KEY_RHEL

    @property
    def url(self):
        return getattr(
            settings, 'rhel{0}_os'.format(self.distro_major_version))


class SatelliteToolsRepository(GenericRHRepository):
    """Satellite Tools Repository"""
    _key = PRODUCT_KEY_SAT_TOOLS

    @property
    def url(self):
        return settings.sattools_repo['{0}{1}'.format(
            PRODUCT_KEY_RHEL, self.distro_major_version
        )]


class SatelliteCapsuleRepository(GenericRHRepository):
    """Satellite capsule repository"""
    _key = PRODUCT_KEY_SAT_CAPSULE

    @property
    def url(self):
        if self.distro == get_server_distro():
            return settings.capsule_repo
        return None


class VirtualizationAgentsRepository(GenericRHRepository):
    """Virtualization Agents repository"""
    _key = PRODUCT_KEY_VIRT_AGENTS
    _distro = DISTRO_RHEL6


class RHELCloudFormsTools(GenericRHRepository):
    _distro = DISTRO_RHEL6
    _key = PRODUCT_KEY_CLOUD_FORMS_TOOLS


class RHELAnsibleEngineRepository(GenericRHRepository):
    """Red Hat Ansible Engine Repository"""
    _key = PRODUCT_KEY_ANSIBLE_ENGINE


class RepositoryCollection(object):
    """Repository collection"""
    _distro = None  # type: str
    _org = None  # type: Dict
    _items = []  # type: List[BaseRepository]
    _repos_info = []  # type: List[Dict]
    _custom_product_info = None  # type: Dict
    _os_repo = None  # type: RHELRepository
    _setup_content_data = None  # type: Dict[str, Dict]

    def __init__(self, distro=None, repositories=None):

        self._items = []

        if distro is not None and distro not in DISTROS_SUPPORTED:
            raise DistroNotSupportedError(
                'distro "{0}" not supported'.format(distro))
        if distro is not None:
            self._distro = distro

        if repositories is None:
            repositories = []
        self.add_items(repositories)

    @property
    def distro(self):   # type: () -> str
        return self._distro

    @property
    def repos_info(self):   # type: () -> List[Dict]
        return self._repos_info

    @property
    def custom_product(self):
        return self._custom_product_info

    @property
    def os_repo(self):  # type: () -> RHELRepository
        return self._os_repo

    @os_repo.setter
    def os_repo(self, repo):  # type: (RHELRepository) -> None
        if self.os_repo is not None:
            raise OnlyOneOSRepositoryAllowed(
                'OS repo already added.(Only one OS repo allowed)')
        if not isinstance(repo, RHELRepository):
            raise ValueError('repo: "{0}" is not an RHEL repo'.format(repo))
        self._os_repo = repo

    @property
    def repos_data(self):   # type: () -> List[Dict]
        return [repo.data for repo in self]

    @property
    def rh_repos(self):  # type: () -> List[BaseRepository]
        return [item for item in self if item.cdn]

    @property
    def custom_repos(self):  # type: () -> List[BaseRepository]
        return [item for item in self if not item.cdn]

    @property
    def rh_repos_info(self):  # type: () -> List[Dict]
        if bz_bug_is_open(1660133):
            return [repo_info
                    for item, repo_info in zip(self._items, self._repos_info) if item.cdn]
        return [
            repo_info
            for repo_info in self._repos_info
            if repo_info['red-hat-repository'] == 'yes'
        ]

    @property
    def custom_repos_info(self):  # type: () -> List[Dict]
        if bz_bug_is_open(1660133):
            return [repo_info
                    for item, repo_info in zip(self._items, self._repos_info) if not item.cdn]
        return [
            repo_info
            for repo_info in self._repos_info
            if repo_info['red-hat-repository'] == 'no'
        ]

    @property
    def setup_content_data(self):
        return self._setup_content_data

    @property
    def need_subscription(self):  # type: () -> bool
        if self.rh_repos:
            return True
        return False

    @property
    def organization(self):
        return self._org

    def add_item(self, item):  # type: (BaseRepository) -> None
        if self._repos_info:
            raise RepositoryAlreadyCreated(
                'Repositories already created can not add more')
        if not isinstance(item, BaseRepository):
            raise ValueError('item "{0}" is not a repository'.format(item))
        if self.distro is not None:
            item.distro = self.distro
        self._items.append(item)
        if isinstance(item, RHELRepository):
            self.os_repo = item

    def add_items(self, items):  # type: (List[BaseRepository]) -> None
        for item in items:
            self.add_item(item)

    def __iter__(self):
        for item in self._items:
            yield item

    def setup(self, org_id, download_policy=DOWNLOAD_POLICY_ON_DEMAND, synchronize=True):
        # type: (int, str, bool) -> Tuple[Dict, List[Dict]]
        """Setup the repositories on server.

        Recommended usage: repository only setup, for full content setup see
            setup_content.
        """
        if self._repos_info:
            raise RepositoryAlreadyCreated('Repositories already created')
        custom_product = None
        repos_info = []
        if any(not repo.cdn for repo in self):
            custom_product = make_product_wait({'organization-id': org_id})
        custom_product_id = custom_product['id'] if custom_product else None
        for repo in self:
            repo_info = repo.create(org_id, custom_product_id,
                                    download_policy=download_policy, synchronize=synchronize)
            repos_info.append(repo_info)
        self._custom_product_info = custom_product
        self._repos_info = repos_info
        return custom_product, repos_info

    def _setup_content_view(self, org_id, lce_id):
        # type: (int, int) -> Tuple[Dict, Dict]
        """Setup organization content view by adding all the repositories, publishing and promoting
        to lce if needed.
        """
        lce = LifecycleEnvironment.info({
            'id': lce_id,
            'organization-id': org_id,
        })
        content_view = make_content_view({'organization-id': org_id})
        # Add repositories to content view
        for repo in self:
            repo.add_to_content_view(org_id, content_view['id'])
        # Publish the content view
        ContentView.publish({'id': content_view['id']})
        if lce['name'] != ENVIRONMENT:
            # Get the latest content view version id
            content_view_version = ContentView.info({
                'id': content_view['id']
            })['versions'][-1]
            # Promote content view version to lifecycle environment
            ContentView.version_promote({
                'id': content_view_version['id'],
                'organization-id': org_id,
                'to-lifecycle-environment-id': lce_id,
            })
        content_view = ContentView.info({'id': content_view['id']})
        return content_view, lce

    @staticmethod
    def setup_activation_key(org_id, content_view_id, lce_id, subscription_names=None):
        # type: (int, int, int, Optional[List[str]], Optional[str]) -> Dict
        """Create activation and associate content-view, lifecycle environment and subscriptions"""
        if subscription_names is None:
            subscription_names = []
        activation_key = make_activation_key({
            'organization-id': org_id,
            'lifecycle-environment-id': lce_id,
            'content-view-id': content_view_id,
        })
        # Add subscriptions to activation-key
        # Get organization subscriptions
        subscriptions = Subscription.list({'organization-id': org_id}, per_page=False)
        added_subscription_names = []
        for subscription in subscriptions:
            if (subscription['name'] in subscription_names
                    and subscription['name'] not in added_subscription_names):
                ActivationKey.add_subscription({
                    'id': activation_key['id'],
                    'subscription-id': subscription['id'],
                    'quantity': 1,
                })
                added_subscription_names.append(subscription['name'])
                if len(added_subscription_names) == len(subscription_names):
                    break
        missing_subscription_names = set(subscription_names).difference(
            set(added_subscription_names))
        if missing_subscription_names:
            raise ValueError('Missing subscriptions: {0}'.format(missing_subscription_names))
        return activation_key

    @staticmethod
    def organization_has_manifest(organization_id):
        """Check if an organization has a manifest, an organization has manifest if one of it's
        subscriptions have the account defined.
        """
        subscriptions = Subscription.list({'organization-id': organization_id}, per_page=False)
        return any(bool(sub['account']) for sub in subscriptions)

    def setup_content(
            self, org_id, lce_id, upload_manifest=False,
            download_policy=DOWNLOAD_POLICY_ON_DEMAND, rh_subscriptions=None
    ):
        # type: (int, int, bool, str, Optional[List[str]]) -> Dict[str, Any]
        """
        Setup content view and activation key of all the repositories.

        :param org_id: The organization id
        :param lce_id:  The lifecycle environment id
        :param upload_manifest: Whether to upload the manifest (The manifest is
            uploaded only if needed)
        :param download_policy: The repositories download policy
        :param rh_subscriptions: The RH subscriptions to be added to activation
            key
        """
        if self._repos_info:
            raise RepositoryAlreadyCreated(
                'Repositories already created can not setup content')
        if rh_subscriptions is None:
            rh_subscriptions = []
        if self.need_subscription:
            # upload manifest only when needed
            if upload_manifest and not self.organization_has_manifest(org_id):
                manifests.upload_manifest_locked(org_id, interface=manifests.INTERFACE_CLI)
            if not rh_subscriptions:
                # add the default subscription if no subscription provided
                rh_subscriptions = [DEFAULT_SUBSCRIPTION_NAME]
        custom_product, repos_info = self.setup(org_id=org_id, download_policy=download_policy)
        content_view, lce = self._setup_content_view(org_id, lce_id)
        custom_product_name = custom_product['name'] if custom_product else None
        subscription_names = list(rh_subscriptions)
        if custom_product_name:
            subscription_names.append(custom_product_name)
        activation_key = self.setup_activation_key(
            org_id, content_view['id'], lce_id,
            subscription_names=subscription_names,
        )
        setup_content_data = dict(
            activation_key=activation_key,
            content_view=content_view,
            product=custom_product,
            repos=repos_info,
            lce=lce
        )
        self._org = Org.info({'id': org_id})
        self._setup_content_data = setup_content_data
        return setup_content_data

    def setup_virtual_machine(
            self, vm, patch_os_release=False, install_katello_agent=True,
            enable_rh_repos=True, enable_custom_repos=False, configure_rhel_repo=False):
        # type: (VirtualMachine, bool, bool, bool, bool, bool) -> None
        """
        Setup The virtual machine basic task, eg: install katello ca,
        register vm host, enable rh repos and install katello-agent

        :param vm: The Virtual machine to setup.
        :param patch_os_release: whether to patch the VM with os version.
        :param install_katello_agent: whether to install katello-agent
        :param enable_rh_repos: whether to enable RH repositories
        :param enable_custom_repos: whether to enable custom repositories
        :param configure_rhel_repo: Whether to configure the distro Red Hat repository, this is
            needed to configure manually RHEL custom repo url as sync time is very big
            (more than 2 hours for RHEL 7Server) and not critical for some contexts.
        """
        if not self._setup_content_data:
            raise ReposContentSetupWasNotPerformed(
                'Repos content setup was not performed')

        patch_os_release_distro = None
        if patch_os_release and self.os_repo:
            patch_os_release_distro = self.os_repo.distro
        rh_repos_id = []  # type: List[str]
        if enable_rh_repos:
            rh_repos_id = [
                getattr(repo, 'rh_repository_id') for repo in self.rh_repos]
        custom_repos_label = []   # type: List[str]
        if enable_custom_repos:
            custom_repos_label = [
                repo['label'] for repo in self.custom_repos_info]

        setup_virtual_machine(
            vm,
            self.organization['label'],
            rh_repos_id=rh_repos_id,
            repos_label=custom_repos_label,
            product_label=self.custom_product[
                'label'] if self.custom_product else None,
            activation_key=self._setup_content_data['activation_key']['name'],
            patch_os_release_distro=patch_os_release_distro,
            install_katello_agent=install_katello_agent
        )
        if configure_rhel_repo:
            rhel_repo_option_name = 'rhel{0}_repo'.format(DISTROS_MAJOR_VERSION[self.distro])
            rhel_repo_url = getattr(settings, rhel_repo_option_name, None)
            if not rhel_repo_url:
                raise ValueError(
                    'Settings option "{0}" is whether not set or does not exist'.format(
                        rhel_repo_option_name))
            vm.configure_rhel_repo(rhel_repo_url)
