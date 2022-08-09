"""Tests for module ``robottelo.helpers``."""
import pytest

from robottelo.helpers import slugify_component
from robottelo.helpers import Storage
from robottelo.utils import validate_ssh_pub_key


class FakeSSHResult:
    def __init__(self, stdout=None, status=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr
        self.status = status


class TestPubKey:
    @pytest.mark.parametrize(
        'invalid_key',
        [
            "ssh-rsa1 xxxxxx user@host",  # rsa1 is unsafe
            "foo bar blaz",  # not a valid type
            "ssh-rsa /gfdgdf/fsdfsdfsdf/@ user@host",  # not valid base64 data
            "sdhsfbghjsbgjhbg user@host",  # not a valid format
        ],
        ids=['rsa1', 'foo', 'base64', 'format'],
    )
    def test_invalid_ssh_pub_keys(self, invalid_key):
        assert not validate_ssh_pub_key(invalid_key)

    @pytest.mark.parametrize(
        'valid_key',
        [
            (
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDuMCPmX7iBXAxH5oLznswA5cc"
                "fV/FABwIWnYl0OYRkDhv3mu9Eogk4H6sCguq4deJtRkwg2C3yEmsNYfBWYu4y5Rk"
                "I4TH/k3N161wn91nBxs/+wqoN3g9tUuWrf98PG4NnYvmZU67RuiSUNXpgLEPfo8j"
                "MKkJ5veKu++DmHdpfqFB9ljWEfWz+kAAKgwo251VRDaKwFsb91LbLFpqn9rfMJUB"
                "hOn+Uebfd0TrHzw08gbVmvfAn61isvFVhvIJBTjNSWsBIm8SuCvhH+inYOwttfE8"
                "FGeR1KSp9Xl0PCYDK0BwvQO3qwD+nehsEUR/FJUXm1IZPc8fi17ieGgPOnrgf"
                " user@new-host"
            ),
            (
                "ssh-dss AAAAB3NzaC1kc3MAAACBAMzXU0Jl0fRCKy5B7R8KVKMLJYuhVPagBSi7"
                "UxRAiVHOHzscQzt5wrgRqknuQ9/xIAVAMUVy3ND5zBLkqKwGm9DKGeYEv7xxDi6Z"
                "z5QjsI9oSSqFSMauDxgl+foC4QPrIlUvb9ez5bVg6aJHKJEngDo+lvfVROgQOvTx"
                "I9IXn7oLAAAAFQCz4jDBOnTjkWXgw8sT46HM1jK4SwAAAIAS2BvUlEevY+2YOiqD"
                "SRy9Dhr+/bWLuLl7oUTEnxPhCyo8paaU0fJO1w3BUsbO3Rg4sBgXChRNyg7iKriB"
                "WbPH6EK1e6IcYv8wUdobB3wg+RJlYU2cq7V8HcPJh+hfAGfMD6UnTDLg+P5SCEW7"
                "Ag+knZNwfKv9IAtd0W86EFdVWwAAAIEAkj5boIRqLiUGbRipEzWzZbWMis2S8Ji2"
                "oR6fUD/h6bZ5ta8nEWApri5OQExK7upelTjSR+MHEDRmeepchkTX0LOjBkZgsPyb"
                "6nEpQUQUJAuns8yAnhsKuEuZmlAGwXOSKiD/KRyJu4KjbbV4oyKXU1fF70zPLmOT"
                "fyvserP5qyo= user@new-host"
            ),
            (
                "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAy"
                "NTYAAABBBPWuLEsYvplkL6XR5wbxzXyzw8tLE/JjLXlzUgxv4LhJN4iufXLPSOvj"
                "sk0ek1TE059poyy5ps+GU2DkisSUVYA= user@new-host"
            ),
        ],
        ids=['rsa', 'dss', 'ecdsa'],
    )
    def test_valid_ssh_pub_keys(self, valid_key):
        assert validate_ssh_pub_key(valid_key)


class TestStorage:
    def test_dict_converted_to_storage(self):
        d = {'key': 'value'}
        storage = Storage(d)
        assert storage.key == 'value'

    def test_multiple_dicts_converted_to_storage(self):
        d = {'key': 'value'}
        e = {'another_key': 'another value'}
        storage = Storage(d, e, spare_argument='one more value')
        assert storage.key == 'value'
        assert storage.another_key == 'another value'
        assert storage.spare_argument == 'one more value'


def test_slugify_component():
    """Assert slugify_component returns proper values"""
    assert slugify_component('ContentViews') == 'contentviews'
    assert slugify_component('File-Management') == 'file-management'
    assert slugify_component('File-Management', False) == 'file_management'
    assert slugify_component('File&Management') == 'filemanagement'
    assert slugify_component('File and Management') == 'filemanagement'
