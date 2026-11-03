"""Strict, dependency-free exact-candidate preparation and runtime evidence.

The caller authenticates registries and deploys between prepare and verify. Evidence
is local JSON, not a test-suite result. Verification covers *all* running containers
visible to the host's podman context; use a dedicated host. No snap lookup occurs.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import tempfile

CORE_COMPONENTS = frozenset(
    ('candlepin', 'foreman', 'foreman-proxy', 'pulp', 'postgresql', 'valkey')
)
# Explicit SatLab choose-installation-source supported names (not an iop-* wildcard).
IOP_COMPONENTS = frozenset(
    (
        'iop-advisor-backend',
        'iop-advisor-frontend',
        'iop-gateway',
        'iop-host-inventory',
        'iop-host-inventory-frontend',
        'iop-ingress',
        'iop-insights-engine',
        'iop-kafka',
        'iop-puptoo',
        'iop-remediations',
        'iop-vmaas',
        'iop-vulnerability-engine',
        'iop-vulnerability-frontend',
        'iop-yuptoo',
    )
)
SUPPORTED_COMPONENTS = CORE_COMPONENTS | IOP_COMPONENTS | {'foreman-mcp-server'}
# Kafka is the independently released IOP dependency, not an IOP application image.
RELEASED_COMPONENTS = frozenset(('postgresql', 'valkey', 'iop-kafka'))
COMPOSE_BASE = (
    'https://download-01.beak-001.prod.iad2.dc.redhat.com/rhel-10/nightly/Satellite/Stream/'
)
HEX64 = r'[0-9a-f]{64}'
IMAGE = (
    r'(registry\.stage\.redhat\.io|registry\.redhat\.io)/'
    r'[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*'
    r'@sha256:' + HEX64
)
RPM_COMMAND = ['rpm', '-qa', '--qf', '%{NAME}\t%{EPOCHNUM}\t%{VERSION}\t%{RELEASE}\t%{ARCH}\n']
REGISTRY_AUTH_FILE = '/etc/foreman/registry-auth.json'


class CandidateError(ValueError):
    """The manifest or observed runtime does not satisfy the candidate contract."""


class CandidateCommandError(RuntimeError):
    """A remote operation failed or returned an invalid result."""


def _require(condition, message):
    if not condition:
        raise CandidateError(message)


def _matches(pattern, value):
    return type(value) is str and re.fullmatch(pattern, value) is not None


def _keys(value, expected, label):
    _require(type(value) is dict and set(value) == set(expected), f'Invalid {label} fields')


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_object, parse_constant=_bad_constant)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise CandidateError('Invalid JSON') from exc


def _bad_constant(value):
    raise CandidateError(f'Invalid JSON constant: {value}')


def _validate(candidate):
    _keys(
        candidate,
        (
            'schema_version',
            'application',
            'oci_revision',
            'snapshot',
            'compose',
            'images',
            'required_running_components',
        ),
        'manifest',
    )
    _require(
        type(candidate['schema_version']) is int and candidate['schema_version'] == 1,
        'schema_version must be integer 1',
    )
    _require(
        type(candidate['application']) is str
        and candidate['application'] == 'satellite-stream-rhel-10',
        'Invalid application',
    )
    _require(_matches(r'[0-9a-f]{40}', candidate['oci_revision']), 'Invalid OCI revision')
    snapshot = candidate['snapshot']
    _require(
        _matches(r'satellite-tenant/[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', snapshot), 'Invalid snapshot'
    )
    dns = snapshot.split('/')[1]
    _require(
        len(dns) <= 253
        and all(
            _matches(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in dns.split('.')
        ),
        'Invalid snapshot DNS name',
    )
    compose = candidate['compose']
    _keys(compose, ('compose_id', 'compose_url', 'host_repo_url'), 'compose')
    _require(
        _matches(r'Satellite-Stream-RHEL-10-[0-9]{8}\.n\.[0-9]+', compose['compose_id']),
        'Invalid compose ID',
    )
    _require(
        type(compose['compose_url']) is str
        and compose['compose_url'] == COMPOSE_BASE + compose['compose_id'],
        'Invalid compose URL',
    )
    _require(
        type(compose['host_repo_url']) is str
        and compose['host_repo_url'] == compose['compose_url'] + '/compose/Satellite/x86_64/os/',
        'Invalid host repository URL',
    )
    images = candidate['images']
    _require(
        type(images) is dict
        and images.keys() >= CORE_COMPONENTS
        and images.keys() <= SUPPORTED_COMPONENTS,
        'Missing core or unsupported images',
    )
    for component, uri in images.items():
        _require(_matches(IMAGE, uri), f'Invalid digest URI for {component}')
        _require(
            not uri.startswith('registry.redhat.io/') or component in RELEASED_COMPONENTS,
            f'Production registry not allowed for {component}',
        )
    _require(
        len(set(images.values())) == len(images),
        'Distinct components require distinct image references',
    )
    required = candidate['required_running_components']
    _require(
        type(required) is list and all(type(item) is str for item in required),
        'required_running_components must be a list of strings',
    )
    _require(
        len(required) == len(set(required))
        and set(required) >= CORE_COMPONENTS
        and set(required) <= images.keys(),
        'Missing, duplicate or unknown required components',
    )
    return candidate


def load_candidate(path, expected_sha256):
    """Verify raw-file SHA256 *before* JSON parsing, then return a validated dict."""
    _require(_matches(HEX64, expected_sha256), 'Invalid expected manifest SHA256')
    raw = Path(path).read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'Manifest SHA256 mismatch')
    return _validate(_json(raw))


def _execute(host, argv):
    command = shlex.join(argv)
    try:
        result = host.execute(command)
    except Exception as exc:
        raise CandidateCommandError(f'Command failed: {command}') from exc
    if (
        type(getattr(result, 'status', None)) is not int
        or result.status != 0
        or type(getattr(result, 'stdout', None)) is not str
    ):
        raise CandidateCommandError(f'Command failed or malformed response: {command}')
    return result.stdout


def prepare_candidate(host, candidate):
    """Pull every exact image, then write Quadlet overrides; return None.

    Does not authenticate, deploy, reload systemd, or roll back partial preparation.
    """
    _validate(candidate)
    for uri in candidate['images'].values():
        _execute(host, ['podman', 'pull', '--authfile', REGISTRY_AUTH_FILE, uri])
    for component, uri in candidate['images'].items():
        directory = f'/etc/containers/systemd/{component}.image.d'
        _execute(host, ['mkdir', '-p', directory])
        try:
            host.put(
                f'[Image]\nImage={uri}\n\n[Service]\nEnvironment=REGISTRY_AUTH_FILE={REGISTRY_AUTH_FILE}\n',
                f'{directory}/override.conf',
                temp_file=True,
            )
        except Exception as exc:
            raise CandidateCommandError(f'Cannot write override for {component}') from exc


def _inspect(host, argv):
    value = _json(_execute(host, argv))
    _require(
        type(value) is list and len(value) == 1 and type(value[0]) is dict,
        'Expected one inspect object',
    )
    return value[0]


def _running_ids(host):
    ids = _execute(host, ['podman', 'ps', '--no-trunc', '--quiet']).splitlines()
    _require(
        ids and all(_matches(HEX64, item) for item in ids) and len(ids) == len(set(ids)),
        'Empty or invalid running container set',
    )
    return ids


def _inventory(host, prefix=()):
    raw = _execute(host, [*prefix, *RPM_COMMAND])
    lines = raw.splitlines()
    _require(
        lines and all(len(line.split('\t')) == 5 and all(line.split('\t')) for line in lines),
        'Empty or malformed RPM inventory',
    )
    return sorted(lines)


def verify_candidate(host, candidate, evidence_path, manifest_sha256):
    """Verify actual running image IDs against RepoDigests and write local evidence.

    Returns the evidence dict. The caller supplies the SHA256 used by load_candidate
    and must not mutate its returned dict. An existing evidence path is refused to
    prevent stale/overwritten success evidence. Inventory failures are fatal,
    including images without rpm. This is a point-in-time check, not attestation
    against a compromised host or proof of component health/test-suite success.
    """
    _validate(candidate)
    _require(_matches(HEX64, manifest_sha256), 'Invalid manifest SHA256')
    path = Path(evidence_path)
    _require(not path.exists(), 'Evidence path already exists; use a fresh path')
    ids = _running_ids(host)
    observations = []
    represented = set()
    for container_id in ids:
        container = _inspect(host, ['podman', 'inspect', '--type', 'container', container_id])
        _require(container.get('Id') == container_id, 'Container inspect identity mismatch')
        state = container.get('State')
        _require(type(state) is dict and state.get('Running') is True, 'Container is not running')
        image_id = container.get('Image')
        _require(_matches(r'(?:sha256:)?' + HEX64, image_id), 'Invalid running image ID')
        image = _inspect(host, ['podman', 'image', 'inspect', image_id])
        inspected_id = image.get('Id')
        _require(
            _matches(r'(?:sha256:)?' + HEX64, inspected_id)
            and inspected_id.removeprefix('sha256:') == image_id.removeprefix('sha256:'),
            'Image inspect identity mismatch',
        )
        digests = image.get('RepoDigests')
        _require(
            type(digests) is list
            and digests
            and all(type(item) is str and item for item in digests),
            'Missing or invalid running RepoDigests',
        )
        components = sorted(key for key, uri in candidate['images'].items() if uri in digests)
        _require(components, 'Unlisted running image or expected RepoDigest missing')
        represented.update(components)
        observations.append(
            {
                'container_id': container_id,
                'image_id': image_id,
                'repo_digests': digests,
                'components': components,
                'rpm_inventory': _inventory(host, ['podman', 'exec', container_id]),
            }
        )
    _require(
        set(candidate['required_running_components']) <= represented,
        'Required runtime component image missing',
    )
    host_inventory = _inventory(host)
    _require(
        set(_running_ids(host)) == set(ids), 'Running container set changed during verification'
    )
    evidence = {
        'schema_version': 1,
        'manifest_sha256': manifest_sha256,
        'application': candidate['application'],
        'oci_revision': candidate['oci_revision'],
        'snapshot': candidate['snapshot'],
        'compose': candidate['compose'],
        'expected_images': candidate['images'],
        'required_running_components': candidate['required_running_components'],
        'running': observations,
        'host_rpm_inventory': host_inventory,
    }
    # Publish only a fully written file, without replacing concurrent/stale evidence.
    # The temporary file shares the destination filesystem for atomic hard linking.
    payload = json.dumps(evidence, indent=2, sort_keys=True) + '\n'
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=path.parent, prefix='.candidate-', delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.link(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return evidence
