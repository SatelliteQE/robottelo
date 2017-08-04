"""Manifest clonning tools.."""
import json
import requests
import six
import time
import uuid
import zipfile

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from nailgun import entities

from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import INTERFACE_API, INTERFACE_CLI
from robottelo.decorators.func_locker import lock_function
from robottelo.ssh import upload_file


class ManifestCloner(object):
    """Manifest clonning utility class."""
    def __init__(self, template=None, signing_key=None):
        self.template = template
        self.signing_key = signing_key

    def _download_manifest_info(self):
        """Download and cache the manifest information."""
        self.template = requests.get(settings.fake_manifest.url).content
        self.signing_key = requests.get(settings.fake_manifest.key_url).content
        self.private_key = serialization.load_pem_private_key(
            self.signing_key,
            password=None,
            backend=default_backend()
        )

    def clone(self):
        """Clones a RedHat-manifest file.

        Change the consumer ``uuid`` and sign the new manifest with
        signing key. The certificate for the key must be installed on the
        candlepin server in order to accept uploading the cloned
        manifest.

        :return: A file-like object (``BytesIO`` on Python 3 and
            ``StringIO`` on Python 2) with the contents of the cloned
            manifest.
        """
        if self.signing_key is None or self.template is None:
            self._download_manifest_info()

        template_zip = zipfile.ZipFile(six.BytesIO(self.template))
        # Extract the consumer_export.zip from the template manifest.
        consumer_export_zip = zipfile.ZipFile(
            six.BytesIO(template_zip.read('consumer_export.zip')))

        # Generate a new consumer_export.zip file changing the consumer
        # uuid.
        consumer_export = six.BytesIO()
        with zipfile.ZipFile(consumer_export, 'w') as new_consumer_export_zip:
            for name in consumer_export_zip.namelist():
                if name == 'export/consumer.json':
                    consumer_data = json.loads(
                        consumer_export_zip.read(name).decode('utf-8'))
                    consumer_data['uuid'] = six.text_type(uuid.uuid1())
                    new_consumer_export_zip.writestr(
                        name,
                        json.dumps(consumer_data)
                    )
                else:
                    new_consumer_export_zip.writestr(
                        name,
                        consumer_export_zip.read(name)
                    )

        # Generate a new manifest.zip file with the generated
        # consumer_export.zip and new signature.
        manifest = six.BytesIO()
        with zipfile.ZipFile(
                manifest, 'w', zipfile.ZIP_DEFLATED) as manifest_zip:
            consumer_export.seek(0)
            manifest_zip.writestr(
                'consumer_export.zip',
                consumer_export.read()
            )
            consumer_export.seek(0)
            signer = self.private_key.signer(
                padding.PKCS1v15(), hashes.SHA256())
            signer.update(consumer_export.read())
            manifest_zip.writestr(
                'signature',
                signer.finalize()
            )
        # Make sure that the file-like object is at the beginning and
        # ready to be read.
        manifest.seek(0)
        return manifest

    def original(self):
        """Returns the original manifest as a file-like object.

        Be aware that using the original manifest and not removing it
        afterwards will make impossible to import it on any other Organization.

        Make sure to close the returned file-like object in order to clean up
        the memory used to store it.
        """
        if self.signing_key is None or self.template is None:
            self._download_manifest_info()
        return six.BytesIO(self.template)


# Cache the ManifestCloner in order to avoid downloading the manifest template
# every single time.
_manifest_cloner = ManifestCloner()


class Manifest(object):
    """Class that holds the contents of a manifest with a generated filename
    based on ``time.time``.

    To ensure that the manifest content is closed use this class as a context
    manager with the ``with`` statement::

        with Manifest() as manifest:
            # my fancy stuff
    """
    def __init__(self, content=None, filename=None):
        self._content = content
        self.filename = filename

        if self._content is None:
            self._content = _manifest_cloner.clone()
        if self.filename is None:
            self.filename = u'/var/tmp/manifest-{0}.zip'.format(
                    int(time.time()))

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


def clone():
    """Clone the cached manifest and return a ``Manifest`` object.

    Is hightly recommended to use this with the ``with`` statement to make that
    the content of the manifest (file-like object) is closed properly::

        with clone() as manifest:
            # my fancy stuff
    """
    return Manifest()


def original_manifest():
    """Returns a ``Manifest`` object filed with the template manifest.

    Make sure to remove the manifest after its usage otherwiser the Satellite 6
    server will not accept it anymore on any other organization.

    Is hightly recommended to use this with the ``with`` statement to make that
    the content of the manifest (file-like object) is closed properly::

        with original_manifest() as manifest:
            # my fancy stuff
    """
    return Manifest(_manifest_cloner.original())


@lock_function
def upload_manifest_locked(org_id, manifest,  interface=INTERFACE_API):
    """Upload a manifest with locking, using the requested interface.

    :type org_id: int
    :type manifest: robottelo.manifests.Manifest
    :type interface: str

    :returns: the upload result

    Note: The manifest uploading is strictly locked only when using this
        function

    Usage::

        # for API interface
        manifest = manifests.clone()
        upload_manifest_locked(org_id, manifest, interface=INTERFACE_API)

        # for CLI interface
        manifest = manifests.clone()
        upload_manifest_locked(org_id, manifest, interface=INTERFACE_CLI)

        # or in one line with default interface
        result = upload_manifest_locked(org_id, manifests.clone())
        subscription_id = result[id']
    """

    if interface not in [INTERFACE_API, INTERFACE_CLI]:
        raise ValueError(
            'upload manifest with interface "{0}" not supported'
            .format(interface)
        )
    if interface == INTERFACE_API:
        with manifest:
            result = entities.Subscription().upload(
                data={'organization_id': org_id},
                files={'content': manifest.content},
            )
    else:
        # interface is INTERFACE_CLI
        with manifest:
            upload_file(manifest.content, manifest.filename)

        result = Subscription.upload({
            'file': manifest.filename,
            'organization-id': org_id,
        })

    return result
