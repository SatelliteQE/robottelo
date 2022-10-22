"""A collection of mixins for robottelo.hosts classes"""
import json
from functools import cached_property
from tempfile import NamedTemporaryFile

import requests
from box import Box

from robottelo import constants
from robottelo.api import utils
from robottelo.config import robottelo_tmp_dir
from robottelo.errors import InvalidArgumentError
from robottelo.errors import RepositoryDataNotFound


class VersionedContent:
    """Helpers mixin focused around content specific to a host's version"""

    @cached_property
    def _v_major(self):
        return self.os_version.major

    @cached_property
    def REPOSET(self):
        return {
            'rhel': constants.REPOSET[f'rhel{self._v_major}'],
            'rhst': constants.REPOSET[f'rhst{self._v_major}'],
        }

    @cached_property
    def REPOS(self):
        return {
            'rhel': constants.REPOS[f'rhel{self._v_major}'],
            'rhscl': constants.REPOS[f'rhscl{self._v_major}'],
            'rhst': constants.REPOS[f'rhst{self._v_major}'],
            'rhsc': constants.REPOS[f'rhsc{self._v_major}'],
            'rhsc_iso': constants.REPOS[f'rhsc{self._v_major}_iso'],
        }

    @cached_property
    def OSCAP(self):
        return {
            'default_content': constants.OSCAP_DEFAULT_CONTENT[f'rhel{self._v_major}_content'],
            'dsrhel': constants.OSCAP_PROFILE[f'dsrhel{self._v_major}'],
            'cbrhel': constants.OSCAP_PROFILE[f'cbrhel{self._v_major}'],
        }

    def _ohsnap_repo_url(self, request_type, product=None, release=None, snap='', os_release=None):
        """Returns a URL pointing to Ohsnap "repo_file" or "repositories" API endpoint"""
        if request_type not in ['repo_file', 'repositories']:
            raise InvalidArgumentError('Type must be one of "repo_file" or "repositories"')
        from robottelo.config import settings

        if not os_release:
            os_release = str(self._v_major)
        if not product:
            if self.__class__.__name__ == 'ContentHost':
                product = 'client'
                release = release or 'Client'
            else:
                product = self.__class__.__name__.lower()
        release = self.satellite.version if not release else str(release)

        if release.lower != 'client':
            release = release.split('.')
            if len(release) == 2:
                release.append('0')
            release = '.'.join(release[:3])  # keep only major.minor.patch
        snap = str(snap or settings.server.version.get("snap"))
        return (
            f'{settings.repos.ohsnap_repo_host}/api/releases/'
            f'{release}{"/" + snap if snap else ""}/el{os_release}/{product}/{request_type}'
        )

    def dogfood_repofile(self, product=None, release=None, snap=''):
        return self._ohsnap_repo_url('repo_file', product, release, snap)

    def dogfood_repository(
        self, repo=None, arch=None, product=None, release=None, snap='', os_release=None
    ):
        """Returns a repository definition based on the arguments provided"""
        arch = arch or self.arch
        res = requests.get(
            self._ohsnap_repo_url('repositories', product, release, snap, os_release)
        )
        res.raise_for_status()
        if not repo:
            if self.__class__.__name__ == 'ContentHost':
                repo = 'client'
            else:
                repo = self.__class__.__name__.lower()
        try:
            repository = next(r for r in res.json() if r['label'] == repo)
        except StopIteration:
            raise RepositoryDataNotFound(
                f'Repository "{repo}" is not provided by the given product'
            )
        repository['baseurl'] = repository['baseurl'].replace('$basearch', arch)
        # Q: Should we use YumRepository class here? `return YumRepository(**repository)`
        return Box(**repository)

    def download_repofile(self, product=None, release=None, snap=''):
        """Downloads the tools/client, capsule, or satellite repos on the machine"""
        self.execute(
            f'curl -o /etc/yum.repos.d/dogfood.repo {self.dogfood_repofile(product, release, snap)}'
        )

    def enable_tools_repo(self, organization_id):
        return utils.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=organization_id,
            product=constants.PRDS['rhel'],
            repo=self.REPOS['rhst']['name'],
            reposet=self.REPOSET['rhst'],
            releasever=None,
        )

    def enable_rhel_repo(self, organization_id):
        return utils.enable_rhrepo_and_fetchid(
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
