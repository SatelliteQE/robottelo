"""Run without pytest/conftest: uv run --no-project python -m unittest discover -s tests/offline."""

# Stdlib unittest is intentional: no pytest plugins or Robottelo global conftest.
# ruff: noqa: PT009, PT027

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

SPEC = importlib.util.spec_from_file_location(
    'container_candidate',
    Path(__file__).resolve().parents[2] / 'robottelo/utils/container_candidate.py',
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def manifest():
    compose_id = 'Satellite-Stream-RHEL-10-20260720.n.0'
    url = helper.COMPOSE_BASE + compose_id
    return {
        'schema_version': 1,
        'application': 'satellite-stream-rhel-10',
        'oci_revision': 'a' * 40,
        'snapshot': 'satellite-tenant/candidate-123',
        'compose': {
            'compose_id': compose_id,
            'compose_url': url,
            'host_repo_url': url + '/compose/Satellite/x86_64/os/',
        },
        'images': {
            name: f'registry.stage.redhat.io/satellite/{name}@sha256:{i:064x}'
            for i, name in enumerate(sorted(helper.CORE_COMPONENTS), 1)
        },
        'required_running_components': sorted(helper.CORE_COMPONENTS),
    }


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'manifest.json'
        self.evidence = Path(self.temporary.name) / 'evidence.json'
        self.candidate = manifest()
        self.raw = json.dumps(self.candidate).encode()
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.path.write_bytes(self.raw)

    def load(self, candidate):
        raw = json.dumps(candidate).encode()
        self.path.write_bytes(raw)
        return helper.load_candidate(self.path, hashlib.sha256(raw).hexdigest())

    def runtime(self, replicas=False):
        self.ids = [f'{i:064x}' for i in range(20, 26 + int(replicas))]
        self.containers = {}
        self.images = {}
        uris = list(self.candidate['images'].values())
        for index, container_id in enumerate(self.ids):
            image_id = 'sha256:' + f'{100 + index % 6:064x}'
            self.containers[container_id] = {
                'Id': container_id,
                'Image': image_id,
                'State': {'Running': True},
                # Deliberately misleading claimed name: verification must ignore it.
                'ImageName': 'untrusted:latest',
            }
            self.images[image_id] = {'Id': image_id, 'RepoDigests': [uris[index % 6]]}
        self.failure = None

        def execute(command):
            args = shlex.split(command)
            if self.failure and self.failure in command:
                return SimpleNamespace(status=1, stdout='', stderr='failure')
            if args[:2] == ['podman', 'ps']:
                output = '\n'.join(self.ids) + '\n'
            elif args[:2] == ['podman', 'inspect']:
                output = json.dumps([self.containers[args[-1]]])
            elif args[:3] == ['podman', 'image', 'inspect']:
                output = json.dumps([self.images[args[-1]]])
            elif args[0] == 'rpm' or args[:2] == ['podman', 'exec']:
                output = 'package\t0\t1.0\t1.el10\tx86_64\n'
            else:
                raise RuntimeError(f'Unexpected command: {command}')
            return SimpleNamespace(status=0, stdout=output, stderr='')

        return Mock(execute=Mock(side_effect=execute))

    def verify(self, host):
        return helper.verify_candidate(host, self.candidate, self.evidence, self.sha)

    def test_positive_load_candidate(self):
        """:id: 8739ad1d-9ed6-4516-8b56-b7849d0d8d18

        :steps: Load a complete checksummed manifest and allowed released dependencies.
        :expectedresults: Exact validated manifest returned.
        """
        self.assertEqual(helper.load_candidate(self.path, self.sha), self.candidate)
        for key in ('postgresql', 'valkey', 'iop-kafka'):
            with self.subTest(component=key):
                candidate = deepcopy(self.candidate)
                candidate['images'][key] = (
                    'registry.redhat.io/dependencies/image@sha256:' + 'c' * 64
                )
                self.assertEqual(self.load(candidate), candidate)

    def test_negative_checksum_before_parsing(self):
        """:id: dc1f8a7d-c27e-43b6-a289-d38a70f28735

        :steps: Replace the file with corrupt non-JSON bytes.
        :expectedresults: Checksum error occurs before parsing.
        """
        self.path.write_bytes(b'not json')
        with self.assertRaisesRegex(helper.CandidateError, 'SHA256 mismatch'):
            helper.load_candidate(self.path, self.sha)

    def test_negative_manifest_validation(self):
        """:id: ee34f6e2-375a-4e65-9575-58a8535a4478

        :steps: Supply missing cores, wrong primitives, unsafe identities and URLs.
        :expectedresults: Every malformed candidate is rejected.
        """
        cases = [None, [], {}, {'images': self.candidate['images']}]
        for key, value in (
            ('schema_version', True),
            ('schema_version', 1.0),
            ('application', 'other'),
            ('oci_revision', 'A' * 40),
            ('snapshot', 'satellite-tenant/../bad'),
            ('snapshot', 'satellite-tenant/bad;id'),
            ('snapshot', 'satellite-tenant/a..b'),
            ('images', {}),
            ('required_running_components', []),
            ('required_running_components', ['foreman'] * 6),
            ('required_running_components', [None]),
            ('required_running_components', sorted(helper.CORE_COMPONENTS) + ['unknown']),
        ):
            candidate = deepcopy(self.candidate)
            candidate[key] = value
            cases.append(candidate)
        for key in helper.CORE_COMPONENTS:
            candidate = deepcopy(self.candidate)
            del candidate['images'][key]
            cases.append(candidate)
        for uri in (
            'quay.io/satellite/foreman@sha256:' + 'c' * 64,
            'registry.redhat.io/satellite/foreman@sha256:' + 'c' * 64,
            'registry.stage.redhat.io/a:latest',
            'registry.stage.redhat.io/a:tag@sha256:' + 'c' * 64,
            'registry.stage.redhat.io/a/../b@sha256:' + 'c' * 64,
            'registry.stage.redhat.io/a@sha256:' + 'c' * 64 + ';id',
            'user:password@registry.stage.redhat.io/a@sha256:' + 'c' * 64,
        ):
            candidate = deepcopy(self.candidate)
            candidate['images']['foreman'] = uri
            cases.append(candidate)
        for field in self.candidate['compose']:
            candidate = deepcopy(self.candidate)
            candidate['compose'][field] += '/../../evil'
            cases.append(candidate)
        for key in ('iop-unknown', '../foreman', 'foreman;id'):
            candidate = deepcopy(self.candidate)
            candidate['images'][key] = candidate['images']['foreman']
            cases.append(candidate)
        duplicate = deepcopy(self.candidate)
        duplicate['images']['foreman'] = duplicate['images']['candlepin']
        cases.append(duplicate)
        for candidate in cases:
            with self.subTest(candidate=candidate), self.assertRaises(helper.CandidateError):
                self.load(candidate)

    def test_negative_json(self):
        """:id: f7578084-ecfc-4549-a650-c3a619b699ce

        :steps: Load checksummed invalid JSON, duplicate keys and nonfinite numbers.
        :expectedresults: Parsing fails closed.
        """
        for raw in (b'{', b'\xff', b'{"a":1,"a":2}', b'{"a":NaN}'):
            self.path.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(helper.CandidateError):
                helper.load_candidate(self.path, hashlib.sha256(raw).hexdigest())

    def test_positive_prepare_candidate(self):
        """:id: 07986727-4903-4923-8c93-dfabe3c91806

        :steps: Prepare with a mocked host.
        :expectedresults: Every digest pulled and each exact Quadlet override uploaded.
        """
        host = Mock()
        host.execute.return_value = SimpleNamespace(status=0, stdout='')
        helper.prepare_candidate(host, self.candidate)
        expected = [
            shlex.join(['podman', 'pull', '--authfile', '/etc/foreman/registry-auth.json', uri])
            for uri in self.candidate['images'].values()
        ]
        self.assertEqual([call.args[0] for call in host.execute.call_args_list[:6]], expected)
        for component, uri in self.candidate['images'].items():
            host.put.assert_any_call(
                f'[Image]\nImage={uri}\n\n[Service]\nEnvironment=REGISTRY_AUTH_FILE=/etc/foreman/registry-auth.json\n',
                f'/etc/containers/systemd/{component}.image.d/override.conf',
                temp_file=True,
            )
        host.reset_mock()
        host.execute.return_value = SimpleNamespace(status=1, stdout='')
        with self.assertRaises(helper.CandidateCommandError):
            helper.prepare_candidate(host, self.candidate)
        host.put.assert_not_called()
        host.reset_mock()
        invalid = deepcopy(self.candidate)
        invalid['images'] = {}
        with self.assertRaises(helper.CandidateError):
            helper.prepare_candidate(host, invalid)
        host.execute.assert_not_called()

    def test_positive_evidence_with_replicas(self):
        """:id: 3b78d7e0-7f6b-4274-b9bd-febb8d045354

        :steps: Verify six component images and an additional worker sharing an image.
        :expectedresults: Evidence binds identities, digests and all RPM inventories.
        """
        evidence = self.verify(self.runtime(replicas=True))
        self.assertEqual(json.loads(self.evidence.read_text()), evidence)
        self.assertEqual(evidence['manifest_sha256'], self.sha)
        self.assertEqual(evidence['compose'], self.candidate['compose'])
        self.assertEqual(len(evidence['running']), 7)
        self.assertTrue(all(row['rpm_inventory'] for row in evidence['running']))
        self.assertTrue(evidence['host_rpm_inventory'])
        self.assertNotIn('test_success', evidence)

    def test_negative_runtime_evidence(self):
        """:id: 71231dc8-0801-4419-9cde-d97b5ade751b

        :steps: Verify wrong/missing digests, missing components and invalid observations.
        :expectedresults: No evidence file is created on any failure.
        """
        for mode in (
            'empty',
            'missing-component',
            'missing',
            'wrong',
            'null',
            'claimed-only',
            'bad-id',
            'stopped',
            'image-mismatch',
            'malformed-json',
            'empty-inventory',
            'digest-string',
            'digest-element',
            'runtime-drift',
        ):
            with self.subTest(mode=mode):
                host = self.runtime()
                image = next(iter(self.images.values()))
                container = next(iter(self.containers.values()))
                if mode == 'empty':
                    self.ids.clear()
                elif mode == 'missing-component':
                    self.ids.pop()
                elif mode == 'missing':
                    del image['RepoDigests']
                elif mode == 'wrong':
                    image['RepoDigests'] = ['registry.stage.redhat.io/other@sha256:' + 'f' * 64]
                elif mode == 'null':
                    image['RepoDigests'] = None
                elif mode == 'claimed-only':
                    image['RepoDigests'] = []
                    container['ImageName'] = self.candidate['images']['foreman']
                elif mode == 'bad-id':
                    container['Image'] = '$(id)'
                elif mode == 'stopped':
                    container['State']['Running'] = False
                elif mode == 'image-mismatch':
                    image['Id'] = 'sha256:' + 'f' * 64
                elif mode == 'digest-string':
                    image['RepoDigests'] = self.candidate['images']['foreman']
                elif mode == 'digest-element':
                    image['RepoDigests'] = [None]
                elif mode == 'runtime-drift':
                    original = host.execute.side_effect
                    calls = []

                    def changing_set(cmd, original=original, calls=calls):
                        if cmd.startswith('podman ps'):
                            calls.append(cmd)
                            if len(calls) == 2:
                                return SimpleNamespace(status=0, stdout=self.ids[0] + '\n')
                        return original(cmd)

                    host.execute.side_effect = changing_set
                elif mode == 'malformed-json':
                    original = host.execute.side_effect
                    host.execute.side_effect = lambda cmd, original=original: (
                        SimpleNamespace(status=0, stdout='not JSON')
                        if cmd.startswith('podman inspect')
                        else original(cmd)
                    )
                elif mode == 'empty-inventory':
                    original = host.execute.side_effect
                    host.execute.side_effect = lambda cmd, original=original: (
                        SimpleNamespace(status=0, stdout='') if 'rpm' in cmd else original(cmd)
                    )
                with self.assertRaises(helper.CandidateError):
                    self.verify(host)
                self.assertFalse(self.evidence.exists())

    def test_negative_command_failure(self):
        """:id: 5dd4c69f-9526-431d-b84a-70fb66e1e366

        :steps: Fail each category of verification command.
        :expectedresults: Failure is propagated without writing evidence.
        """
        for failure in (
            'podman ps',
            'podman inspect',
            'podman image inspect',
            'podman exec',
            'rpm',
        ):
            with self.subTest(command=failure):
                host = self.runtime()
                self.failure = failure
                with self.assertRaises(helper.CandidateCommandError):
                    self.verify(host)
                self.assertFalse(self.evidence.exists())
        host = self.runtime()
        host.execute.side_effect = None
        host.execute.return_value = None
        with self.assertRaises(helper.CandidateCommandError):
            self.verify(host)
        self.assertFalse(self.evidence.exists())


if __name__ == '__main__':
    unittest.main()
