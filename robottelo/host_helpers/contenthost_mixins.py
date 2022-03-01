"""A collection of mixins for robottelo.hosts classes"""
import json
from functools import cached_property
from tempfile import NamedTemporaryFile

from robottelo import constants
from robottelo.api import utils
from robottelo.config import robottelo_tmp_dir


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

    # pull from settings.server.repos???

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
