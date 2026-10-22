"""Offline tests of the actual host wiring without loading lab configuration."""

import ast
from functools import lru_cache
from pathlib import Path
import types
import unittest
from unittest.mock import MagicMock, patch

import pytest


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class CandidateHostContractTest(unittest.TestCase):
    def setUp(self):
        self.server = AttrDict(
            candidate_manifest='/tmp/candidate.json',
            candidate_sha256='a' * 64,
            candidate_evidence='/tmp/evidence.json',
            version=AttrDict(rhel_version='10', source='nightly'),
            deploy_arguments={},
            deploy_workflows=AttrDict(os='deploy-rhel'),
            admin_username='test-admin',
            admin_password='test-password',
        )
        self.settings = AttrDict(server=self.server, flavors=AttrDict(default='test-flavor'))
        self.candidate = {'compose': {'host_repo_url': 'https://example.test/compose/Satellite'}}
        self.helper = types.ModuleType('robottelo.utils.container_candidate')
        self.helper.load_candidate = MagicMock(return_value=self.candidate)
        self.helper.prepare_candidate = MagicMock()
        self.helper.verify_candidate = MagicMock()
        patcher = patch.dict('sys.modules', {'robottelo.utils.container_candidate': self.helper})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.broker = MagicMock(side_effect=lambda **kwargs: MagicMock())
        source = Path(__file__).resolve().parents[2] / 'robottelo/hosts.py'
        tree = ast.parse(source.read_text())
        names = {'lru_sat_ready_rhel', '_lru_sat_ready_rhel', 'install_satellite_foremanctl'}
        definitions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name in names
        ]
        self.namespace = dict(
            settings=self.settings, Broker=self.broker, Satellite=object, lru_cache=lru_cache
        )
        exec(
            compile(ast.Module(body=definitions, type_ignores=[]), str(source), 'exec'),
            self.namespace,
        )

    def test_positive_candidate_cache_identity(self):
        """Normalize RHEL and separate candidates.

        :id: 1dd777a5-cd35-467b-ac56-f4f3182aba6c
        :steps: Request the same OS with matching and changed candidate checksums.
        :expectedresults: Matching candidates reuse one host; different candidates do not.
        """
        get_host = self.namespace['lru_sat_ready_rhel']
        first = get_host(None)
        assert first is get_host('10')
        self.server.candidate_sha256 = 'b' * 64
        assert first is not get_host('10')
        assert self.broker.call_count == 2
        assert self.broker.call_args.kwargs['skip_vm_pooling']

    def test_negative_invalid_candidate_before_provision(self):
        """Reject identity and template conflicts before checkout.

        :id: 54f69875-a8fd-4858-b8a2-eaed3f41ed69
        :steps: Supply a non-EL10 target or a preinstalled Satellite template.
        :expectedresults: No host is provisioned.
        """
        with pytest.raises(ValueError, match='RHEL 10'):
            self.namespace['lru_sat_ready_rhel']('9')
        self.server.deploy_arguments = {'deploy_template_name': 'old-satellite'}
        with pytest.raises(ValueError, match='explicit Satellite template'):
            self.namespace['lru_sat_ready_rhel']('10')
        self.broker.assert_not_called()

    def test_positive_candidate_install_order(self):
        """Use pinned repos/images before deploy and verify afterward.

        :id: 155cf645-95ed-498d-b7f1-f78164f5eedd
        :steps: Execute the install method with mocked host operations and candidate inputs.
        :expectedresults: Legacy repo selection is bypassed; pinned input preparation and evidence run.
        """
        host = MagicMock()
        host.os_version.major = 10
        host.execute.return_value.status = 0
        timeline = []
        host.execute.side_effect = lambda *a, **kw: (
            timeline.append(a[0]) or types.SimpleNamespace(status=0, stderr='')
        )
        self.helper.prepare_candidate.side_effect = lambda *a: timeline.append('prepare')
        self.helper.verify_candidate.side_effect = lambda *a: timeline.append('verify')
        self.namespace['install_satellite_foremanctl'](host)
        host.setup_satellite_repos.assert_not_called()
        host.create_custom_repos.assert_called_once_with(
            satellite_repo=self.candidate['compose']['host_repo_url']
        )
        deploy_index = next(
            i for i, cmd in enumerate(timeline) if cmd.startswith('satellitectl deploy')
        )
        assert timeline.index('prepare') < deploy_index
        assert timeline.index('verify') > deploy_index
        self.helper.verify_candidate.assert_called_once_with(
            host, self.candidate, '/tmp/evidence.json', 'a' * 64
        )

    def test_positive_legacy_install_unchanged(self):
        """Keep noncandidate installation on its existing repository path.

        :id: 291a894d-9928-4890-b013-c8ef09771392
        :steps: Install without candidate settings.
        :expectedresults: The existing repo setup runs and candidate helpers do not.
        """
        self.server.candidate_manifest = ''
        self.server.candidate_sha256 = ''
        host = MagicMock()
        host.execute.return_value.status = 0
        self.namespace['install_satellite_foremanctl'](host)
        host.setup_satellite_repos.assert_called_once()
        self.helper.prepare_candidate.assert_not_called()
        self.helper.verify_candidate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
