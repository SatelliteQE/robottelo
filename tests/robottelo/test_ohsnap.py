"""Tests for module ``robottelo.utils.ohsnap``."""

from unittest import mock

import pytest

from robottelo.utils.ohsnap import (
    container_image_properties,
    ohsnap_container_images,
    parse_container_image_ref,
)

FAKE_IMAGE_DIGEST = 'sha256:0000000000000000000000000000000000000000000000000000000000000001'
FAKE_VCS_REF = 'aleprocne'
SAMPLE_CONTAINER_IMAGES_RESPONSE = {
    'container_images': [
        {
            'image': f'registry.example.com/satellite/foreman-rhel9@{FAKE_IMAGE_DIGEST}',
            'build_date': '2026-01-01T00:00:00Z',
            'vcs_ref': FAKE_VCS_REF,
            'source_url': f'https://git.example.com/org/repo/-/commit/{FAKE_VCS_REF}',
        },
        {
            'image': 'registry.example.com/satellite/pulp-rhel9:1.0.0',
            'build_date': '2026-01-01T00:00:00Z',
            'vcs_ref': 'cafebabe',
            'source_url': 'https://git.example.com/org/repo/-/commit/cafebabe',
        },
    ]
}


@pytest.fixture
def ohsnap():
    return mock.Mock(
        host='https://ohsnap.example.com',
        request_retry=mock.Mock(timeout=1, delay=1),
    )


@pytest.mark.parametrize(
    ('image_ref', 'registry', 'name', 'tag'),
    [
        (
            'registry.example.com/satellite/foreman-rhel9@sha256:aleprocne',
            'registry.example.com',
            'foreman-rhel9',
            'sha256:aleprocne',
        ),
        (
            'registry.example.com/satellite/pulp-rhel9:1.0.0',
            'registry.example.com',
            'pulp-rhel9',
            '1.0.0',
        ),
        (
            'registry.example.com/satellite/candlepin-rhel9',
            'registry.example.com',
            'candlepin-rhel9',
            '',
        ),
        (
            'foreman-rhel9:latest',
            '',
            'foreman-rhel9:latest',
            '',
        ),
    ],
    ids=['digest', 'version-tag', 'no-tag', 'image-only'],
)
def test_parse_container_image_ref(image_ref, registry, name, tag):
    assert parse_container_image_ref(image_ref) == (registry, name, tag)


@mock.patch('robottelo.utils.ohsnap.wait_for')
def test_ohsnap_container_images(mock_wait_for, ohsnap):
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_CONTAINER_IMAGES_RESPONSE
    mock_wait_for.return_value = (mock_response, None)

    images = ohsnap_container_images(ohsnap, 'stream', '1.0')

    assert len(images) == 2
    mock_wait_for.assert_called_once()


@mock.patch('robottelo.utils.ohsnap.wait_for')
def test_ohsnap_container_images_non_200_returns_empty_list(mock_wait_for, ohsnap):
    mock_response = mock.Mock()
    mock_response.status_code = 404
    mock_wait_for.return_value = (mock_response, None)

    assert ohsnap_container_images(ohsnap, 'stream', '1.0') == []


@mock.patch('robottelo.utils.ohsnap.wait_for')
def test_ohsnap_container_images_returns_empty_on_fetch_error(mock_wait_for, ohsnap):
    mock_wait_for.side_effect = RuntimeError('connection failed')

    assert ohsnap_container_images(ohsnap, 'stream', '1.0') == []


@mock.patch('robottelo.utils.ohsnap.ohsnap_container_images')
def test_container_image_properties(mock_container_images, ohsnap):
    mock_container_images.return_value = SAMPLE_CONTAINER_IMAGES_RESPONSE['container_images']

    properties = dict(container_image_properties(ohsnap, 'stream', '1.0'))

    mock_container_images.assert_called_once_with(ohsnap, 'stream', '1.0')
    assert set(properties) == {
        'Container_foreman-rhel9_Image',
        'Container_foreman-rhel9_VCS',
        'Container_pulp-rhel9_Image',
        'Container_pulp-rhel9_VCS',
    }
    assert properties['Container_foreman-rhel9_Image'] == (
        f'registry.example.com/satellite/foreman-rhel9@{FAKE_IMAGE_DIGEST}'
    )
    assert properties['Container_foreman-rhel9_VCS'] == FAKE_VCS_REF
    assert (
        properties['Container_pulp-rhel9_Image']
        == 'registry.example.com/satellite/pulp-rhel9:1.0.0'
    )
    assert properties['Container_pulp-rhel9_VCS'] == 'cafebabe'


@mock.patch('robottelo.utils.ohsnap.ohsnap_container_images')
def test_container_image_properties_returns_empty_when_ohsnap_empty(mock_container_images, ohsnap):
    mock_container_images.return_value = []

    assert container_image_properties(ohsnap, 'stream', '1.0') == []
