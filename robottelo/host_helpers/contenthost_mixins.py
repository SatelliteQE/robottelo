"""A collection of mixins for robottelo.hosts classes"""
from functools import cached_property
import json
from tempfile import NamedTemporaryFile

from robottelo import constants
from robottelo.config import robottelo_tmp_dir, settings
from robottelo.logging import logger
from robottelo.utils.ohsnap import dogfood_repofile_url, dogfood_repository


class VersionedContent:
    """Helpers mixin focused around content specific to a host's version"""

    @cached_property
    def _v_major(self):
        return self.os_version.major

    @cached_property
    def REPOSET(self):
        try:
            if self._v_major > 7:
                sys_reposets = {
                    'rhel_bos': constants.REPOSET[f'rhel{self._v_major}_bos'],
                    'rhel_aps': constants.REPOSET[f'rhel{self._v_major}_aps'],
                }
            else:
                sys_reposets = {
                    'rhel': constants.REPOSET[f'rhel{self._v_major}'],
                    'rhscl': constants.REPOSET[f'rhscl{self._v_major}'],
                }
            reposets = {'rhst': constants.REPOSET[f'rhst{self._v_major}']}
        except KeyError as err:
            raise ValueError(f'Unsupported system version: {self._v_major}') from err
        return sys_reposets | reposets

    @cached_property
    def REPOS(self):
        try:
            if self._v_major > 7:
                sys_repos = {
                    'rhel_bos': constants.REPOS[f'rhel{self._v_major}_bos'],
                    'rhel_aps': constants.REPOS[f'rhel{self._v_major}_aps'],
                }
            else:
                sys_repos = {
                    'rhel': constants.REPOS[f'rhel{self._v_major}'],
                    'rhscl': constants.REPOS[f'rhscl{self._v_major}'],
                }
            repos = {
                'rhsclient': constants.REPOS[f'rhsclient{self._v_major}'],
                'rhsc': constants.REPOS[f'rhsc{self._v_major}'],
            }
            return sys_repos | repos
        except KeyError as err:
            raise ValueError(f'Unsupported system version: {self._v_major}') from err

    @cached_property
    def OSCAP(self):
        return {
            'default_content': constants.OSCAP_DEFAULT_CONTENT[f'rhel{self._v_major}_content'],
            'dsrhel': constants.OSCAP_PROFILE[f'dsrhel{self._v_major}'],
            'cbrhel': constants.OSCAP_PROFILE[f'cbrhel{self._v_major}'],
        }

    def _dogfood_helper(self, product, release, repo=None):
        """Function to return repository related attributes
        based on the input and the host object
        """
        v_major = str(self._v_major)
        if not product:
            if self.__class__.__name__ == 'ContentHost':
                product = 'client'
                release = release or 'client'
            else:
                product = self.__class__.__name__.lower()
        repo = repo or product  # if repo is not specified, set it to the same as the product is
        release = self.satellite.version if not release else str(release)
        # issue warning if requesting repofile of different version than the product is
        settings_release = settings.server.version.release.split('.')
        if len(settings_release) == 2:
            settings_release.append('0')
        settings_release = '.'.join(settings_release)
        if product != 'client' and release != settings_release:
            logger.warning(
                'Satellite release in settings differs from the one passed to the function '
                'or the version of the Satellite object. '
                f'settings: {settings_release}, parameter: {release}'
            )
        return product, release, v_major, repo

    def download_repofile(self, product=None, release=None, snap=''):
        """Downloads the tools/client, capsule, or satellite repos on the machine"""
        product, release, v_major, _ = self._dogfood_helper(product, release)
        url = dogfood_repofile_url(settings.ohsnap, product, release, v_major, snap)
        self.execute(f'curl -o /etc/yum.repos.d/dogfood.repo -L {url}')

    def dogfood_repository(self, repo=None, product=None, release=None, snap=''):
        """Returns a repository definition based on the arguments provided"""
        product, release, v_major, repo = self._dogfood_helper(product, release, repo)
        return dogfood_repository(settings.ohsnap, repo, product, release, v_major, snap, self.arch)

    def enable_tools_repo(self, organization_id):
        return self.satellite.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=organization_id,
            product=constants.PRDS['rhel'],
            repo=self.REPOS['rhst']['name'],
            reposet=self.REPOSET['rhst'],
            releasever=None,
        )

    def enable_rhel_repo(self, organization_id):
        return self.satellite.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=organization_id,
            product=constants.PRDS['rhel'],
            repo=self.REPOS['rhel']['name'],
            reposet=self.REPOSET['rhel'],
            releasever=None,
        )

    def create_custom_html_repo(self, rpm_url, repo_name=None, update=False, remove_rpm=None):
        """Creates a custom yum repository, that will be published on https

        This could be used to quickly create custom repo on satellite to perform repository sync
        testing

        :needs: createrepo rpm to be installed on host system

        :param: str rpm_url : rpm url to wget the rpm
        :param: str repo_name: Name of the repository
        :param: bool update: update the existing repo by adding new rpm and regenerate repomd
        :param: str remove_rpm: Remove rpm before updating the existing the repo
        """
        repo_name = repo_name or 'custom_repo'
        file_path = f'/var/www/html/pub/{repo_name}/'

        if update:
            self.execute(f'wget {rpm_url} -P {file_path}')
            self.execute(f'rm -rf {file_path + remove_rpm}')
            self.execute(f'createrepo --update {file_path}')
        else:
            self.execute(f'rm -rf {file_path}')
            self.execute(f'mkdir {file_path}')
            self.execute(f'wget {rpm_url} -P {file_path}')
            # Renaming custom rpm to preRepoSync.rpm
            self.execute(f'createrepo --database {file_path}')


class HostInfo:
    """Helpers mixin that enables getting information about a host"""

    @property
    def applicable_errata_count(self):
        """return the applicable errata count for a host"""
        self.run('subscription-manager repos')
        return self.nailgun_host.read().content_facet_attributes['errata_counts']['total']


class SystemFacts:
    """Helpers mixin that enables getting/setting subscription-manager facts on a host"""

    def _get_dir_list(self, dir_path, criteria="*"):
        """return a list of all files in a given directory that match the search criteria"""
        return self.execute(f'find {dir_path} -name "{criteria}"').stdout.splitlines()

    def _get_custom_facts(self, filename=None):
        """get a dictionary of custom facts on the system"""
        if isinstance(filename, list):
            all_facts = {}
            for fname in filename:
                all_facts.update(self._get_custom_facts(fname))
        if filename is None:
            filenames = self._get_dir_list('/etc/rhsm/facts/', '*.facts')
            filename = [fname.replace('/etc/rhsm/facts/', '') for fname in filenames]
        if isinstance(filename, str):
            result = self.execute(f'cat /etc/rhsm/facts/{filename}')
            if result.status == 0:
                return {filename: json.loads(result.stdout)}
        return {}

    def get_facts(self):
        """Get a dictionary representation of all subscription-manager facts"""
        result = self.execute('subscription-manager facts')
        fact_dict, last_key = {}, None
        if result.status == 0:
            for line in result.stdout.splitlines():
                if ': ' in line:
                    key, val = line.split(': ')
                else:
                    key = last_key
                    val = f'{fact_dict[key]} {line}'
                fact_dict[key] = val.strip()
                last_key = key
        return fact_dict

    def set_facts(self, facts_dict):
        """Given a facts dictionary, write the contents to the appropriate files
        A single facts dictionary corresponds to a single file.
        The default file is custom.facts, but can be overridden by wrapping the facts dict
        in an outer dictionary where the key is a new name {'my_facts.facts': {<facts dict>}}
        """
        # check if a filename was given
        k, *_ = facts_dict
        if '.facts' not in k:
            # if not, then wrap it all under a custom.facts key
            facts_dict = {'custom.facts': facts_dict}
        for filename, facts in facts_dict.items():
            with NamedTemporaryFile('w+', dir=robottelo_tmp_dir) as tf:
                json.dump(facts, tf)
                tf.flush()
                self.put(tf.name, f'/etc/rhsm/facts/{filename}')
