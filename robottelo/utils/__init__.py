# General utility functions which does not fit into other util modules OR
# Independent utility functions that doesnt need separate module
import base64
import io
import json
import os
import re
import time
import uuid
import zipfile
from pathlib import Path

import requests
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

from robottelo.config import settings
from robottelo.constants import Colored
from robottelo.exceptions import InvalidVaultURLForOIDC


def export_vault_env_vars(filename=None, envdata=None):
    if not envdata:
        envdata = Path(filename or '.env').read_text()
    vaulturl = re.findall('VAULT_URL_FOR_DYNACONF=(.*)', envdata)[0]

    # Vault CLI Env Var
    os.environ['VAULT_ADDR'] = vaulturl

    # Dynaconf Vault Env Vars
    if re.findall('VAULT_ENABLED_FOR_DYNACONF=(.*)', envdata)[0] == 'true':
        if 'localhost:8200' in vaulturl:
            raise InvalidVaultURLForOIDC(
                f"{Colored.REDDARK}{vaulturl} doesnt supports OIDC login,"
                "please change url to corp vault in env file!"
            )


def gen_ssh_keypairs():
    """Generates private SSH key with its public key"""
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    private = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    )
    public = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )
    return private.decode('utf-8'), public.decode('utf-8')


def validate_ssh_pub_key(key):
    """Validates if a string is in valid ssh pub key format
    :param key: A string containing a ssh public key encoded in base64
    :return: Boolean
    """

    if not isinstance(key, str):
        raise ValueError(f"Key should be a string type, received: {type(key)}")

    # 1) a valid pub key has 3 parts separated by space
    # 2) The second part (key string) should be a valid base64
    try:
        key_type, key_string, _ = key.split()  # need more than one value to unpack
        base64.decodebytes(key_string.encode('ascii'))
        return key_type in ('ecdsa-sha2-nistp256', 'ssh-dss', 'ssh-rsa', 'ssh-ed25519')
    except (ValueError, base64.binascii.Error):
        return False


def slugify_component(string, keep_hyphens=True):
    """Make component name a slug
       Arguments:
        string {str} -- Component name e.g: ActivationKeys
        keep_hyphens {bool} -- Keep hyphens or replace with underscores
    return:
        str -- component slug e.g: activationkeys
    """
    string = string.replace(" and ", "&")
    if not keep_hyphens:
        string = string.replace('-', '_')
    return re.sub("[^-_a-zA-Z0-9]", "", string.lower())


# Manifest Cloning
class ManifestCloner:
    """Manifest cloning utility class."""

    def __init__(self, template=None, private_key=None, signing_key=None):
        self.template = template
        self.signing_key = signing_key
        self.private_key = private_key

    def _download_manifest_info(self, name='default'):
        """Download and cache the manifest information."""
        if self.template is None:
            self.template = {}
        self.template[name] = requests.get(settings.fake_manifest.url[name], verify=False).content
        if self.signing_key is None:
            self.signing_key = requests.get(settings.fake_manifest.key_url, verify=False).content
        if self.private_key is None:
            self.private_key = crypto_serialization.load_pem_private_key(
                self.signing_key, password=None, backend=crypto_default_backend()
            )

    def manifest_clone(self, org_environment_access=False, name='default'):
        """Clones a RedHat-manifest file.

        Change the consumer ``uuid`` and sign the new manifest with
        signing key. The certificate for the key must be installed on the
        candlepin server in order to accept uploading the cloned
        manifest.

        :param org_environment_access: Whether to modify consumer content
            access mode to org_environment (Golden ticket enabled manifest).

        :param name: which manifest url to clone (named key-value pairs
            are defined as fake_manifest.url value in robottelo.properties
            (default: 'default')

        :return: A file-like object (``BytesIO`` on Python 3 and
            ``StringIO`` on Python 2) with the contents of the cloned
            manifest.
        """
        if self.signing_key is None or self.template is None or self.template.get(name) is None:
            self._download_manifest_info(name)

        template_zip = zipfile.ZipFile(io.BytesIO(self.template[name]))
        # Extract the consumer_export.zip from the template manifest.
        consumer_export_zip = zipfile.ZipFile(io.BytesIO(template_zip.read('consumer_export.zip')))

        # Generate a new consumer_export.zip file changing the consumer
        # uuid.
        consumer_export = io.BytesIO()
        with zipfile.ZipFile(consumer_export, 'w') as new_consumer_export_zip:
            for name in consumer_export_zip.namelist():
                if name == 'export/consumer.json':
                    consumer_data = json.loads(consumer_export_zip.read(name).decode('utf-8'))
                    consumer_data['uuid'] = str(uuid.uuid1())
                    if org_environment_access:
                        consumer_data['contentAccessMode'] = 'org_environment'
                        consumer_data['owner'][
                            'contentAccessModeList'
                        ] = 'entitlement,org_environment'
                    new_consumer_export_zip.writestr(name, json.dumps(consumer_data))
                else:
                    new_consumer_export_zip.writestr(name, consumer_export_zip.read(name))

        # Generate a new manifest.zip file with the generated
        # consumer_export.zip and new signature.
        manifest = io.BytesIO()
        with zipfile.ZipFile(manifest, 'w', zipfile.ZIP_DEFLATED) as manifest_zip:
            consumer_export.seek(0)
            manifest_zip.writestr('consumer_export.zip', consumer_export.read())
            consumer_export.seek(0)
            signature = self.private_key.sign(
                consumer_export.read(), padding.PKCS1v15(), hashes.SHA256()
            )
            manifest_zip.writestr('signature', signature)
        # Make sure that the file-like object is at the beginning and
        # ready to be read.
        manifest.seek(0)
        return manifest

    def original(self, name='default'):
        """Returns the original manifest as a file-like object.

        :param name: A name of the manifest as defined in robottelo.properties

        Be aware that using the original manifest and not removing it
        afterwards will make it impossible to import it to any other
        Organization.

        Make sure to close the returned file-like object in order to clean up
        the memory used to store it.
        """
        if self.signing_key is None or self.template is None or self.template.get(name) is None:
            self._download_manifest_info(name)
        return io.BytesIO(self.template[name])


# Cache the ManifestCloner in order to avoid downloading the manifest template
# every single time.
_manifest_cloner = ManifestCloner()


class Manifest:
    """Class that holds the contents of a manifest with a generated filename
    based on ``time.time``.

    To ensure that the manifest content is closed use this class as a context
    manager with the ``with`` statement::

        with Manifest() as manifest:
            # my fancy stuff
    """

    def __init__(self, content=None, filename=None, org_environment_access=False, name='default'):
        self._content = content
        self.filename = filename

        if self._content is None:
            self._content = _manifest_cloner.manifest_clone(
                org_environment_access=org_environment_access, name=name
            )
        if self.filename is None:
            self.filename = f'/var/tmp/manifest-{int(time.time())}.zip'

    @property
    def content(self):
        if not self._content.closed:
            # Make sure that the content is always ready to read
            self._content.seek(0)
        return self._content

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if not self.content.closed:
            self.content.close()


def clone(org_environment_access=False, name='default'):
    """Clone the cached manifest and return a ``Manifest`` object.

    :param org_environment_access: Whether to modify consumer content
        access mode to org_environment (Golden ticket enabled manifest).

    :param name: key name of the fake_manifests.url dict defined in
        robottelo.properties

    Is hightly recommended to use this with the ``with`` statement to make that
    the content of the manifest (file-like object) is closed properly::

        with clone() as manifest:
            # my fancy stuff
    """

    return Manifest(org_environment_access=org_environment_access, name=name)


def original_manifest(name='default'):
    """Returns a ``Manifest`` object filed with the template manifest.

    :param name: key name of the fake_manifests.url dict defined in
        robottelo.properties
    """

    return Manifest(_manifest_cloner.original(name=name))
