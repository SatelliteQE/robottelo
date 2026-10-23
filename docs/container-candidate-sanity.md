# Digest-pinned Stream EL10 sanity candidates

Candidate mode is opt-in for foremanctl installation on a fresh RHEL 10 host.
It does not use a numbered OhSnap snap or a preinstalled Satellite template.
Existing installations without candidate settings retain their current behavior.

## Inputs

Set these server settings before collecting/running sanity tests:

- `SERVER.CANDIDATE_MANIFEST`: local path to the complete deployment manifest.
- `SERVER.CANDIDATE_SHA256`: externally supplied SHA-256 of the file's exact bytes.
- `SERVER.CANDIDATE_EVIDENCE`: local output path, default `candidate-evidence.json`.
- `SERVER.VERSION.SOURCE`: `nightly` (also for testing a weekly-marked image candidate).
- `SERVER.VERSION.RHEL_VERSION`: `10`.
- `SERVER.INSTALL_METHOD`: `foremanctl`.

The manifest identifies the exact compose, OCI revision, Snapshot, and component
image digests. It must include the core application images plus PostgreSQL and
Valkey, with all additional images used by the chosen deployment. A core-only
Snapshot inspection record is not a complete deployment manifest. Published
registry references are required; mutable tags and Quay build references are not
accepted by the candidate consumer.

The `compose.host_repo_url` must refer to the same immutable compose's
`Satellite/x86_64/os/` repository. Image build RPMs come from `Satellite-Build`,
which is a different repository. Candidate mode bypasses normal numbered-snap
repository lookup and rejects PR-package overlays.

## Deployment and evidence

The fresh-OS cache includes the manifest checksum. Changing candidates cannot
reuse another candidate's cached host; VM pooling and explicit Satellite template
selection are disabled for this path. Run each candidate in a fresh test process.

After installing `satellitectl`, the consumer writes digest-pinned `.image.d`
overrides and pulls the specified images. After deployment it inspects running
containers and their actual image records. Image IDs are not treated as registry
manifest digests. Missing required images, unlisted running images, wrong digests,
and malformed/empty observations fail validation.

Successful deployment evidence binds the manifest checksum, source identities,
running-image observations, and RPM inventories. It is **not** a sanity approval:
Jenkins must also require a successful nonempty test run, check the same checksum,
and preserve the evidence with the test results. Failed, skipped, aborted, or
zero-test required runs must not approve content.

## Local validation and rollout

Offline helper and host-wiring tests use mocked host operations and never create
VMs. They do not prove that a particular foremanctl version honors every override,
that a registry's multiarchitecture digest is represented as expected by Podman,
or that a changed compose RPM reaches the running image.

A staging run must demonstrate those behaviors, exercise failure cases, and show
that the collected tests use the same verified host before any production trigger
cutover. Jenkins must use an automation image containing this helper; its
candidate preflight imports and validates the manifest to reject older images
that would silently ignore new settings.
