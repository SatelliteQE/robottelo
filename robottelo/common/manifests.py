# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Manifest functions
"""

import logging
import zipfile
import tempfile
import json
import uuid
import shutil
import os
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA


def sign(key_file, file_to_sign):
    """
    Reads the rsa key file and then proceeds to create signed sha256
    hash of the data in the file according to PKCS1 1.5 standard.

    Returns binary signature data.
    """
    with open(key_file) as k:
        key = RSA.importKey(k.read())
        signature = PKCS1_v1_5.new(key)
        with open(file_to_sign, "rb") as data:
            digest = SHA256.new(data.read())
            return signature.sign(digest)


def edit_in_zip(zip_file, file_edit_functions):
    """
    Reads every file in the zip, and for every path in file_edit_functions
    dictionary it applies the relevant function on the contents of the file
    and saves it with new content.

    For example if you had zipfile /tmp/test.zip containing files small.txt,
    filler.txt and large.txt and you'd want small.txt contain 1 and large.txt
    contain 1000, you would call

    edit_in_zip("/tmp/test.zip",
        {'small.txt': lambda x: "1", 'large.txt': lambda x: "1000"})

    """
    tempdir = tempfile.mkdtemp()
    try:
        tempname = os.path.join(tempdir, 'new.zip')
        with zipfile.ZipFile(zip_file, 'r') as zipread:
            with zipfile.ZipFile(tempname, 'w') as zipwrite:
                for item in zipread.infolist():
                    if item.filename not in file_edit_functions:
                        data = zipread.read(item.filename)
                        zipwrite.writestr(item, data)
                    else:
                        data = file_edit_functions[item.filename](
                            zipread.read(item.filename)
                            )
                        zipwrite.writestr(item, data)
        shutil.move(tempname, zip_file)
    finally:
        shutil.rmtree(tempdir)


def edit_consumer(data):
    """
    Takes the string-data of the consumer file and updates with new uuid
    """
    content_dict = json.loads(data)
    content_dict['uuid'] = str(uuid.uuid1())
    return json.dumps(content_dict)


def clone(key_path, old_path, new_path):
    """
    Taking a manifest on oldpath, changes the uuid in consumer.json and resigns
    it with an RSA key. When accompanying certificate is installed on the
    candlepin server, it allows us to quickly create uploadable
    copies of the original manifest.
    """
    shutil.copy(old_path, new_path)
    tempdir = tempfile.mkdtemp()
    with zipfile.ZipFile(new_path) as oldzip:
        oldzip.extractall(tempdir)
        edit_in_zip(tempdir+"/consumer_export.zip",
                    {"/export/consumer.json": edit_consumer})
        signature = sign(key_path, tempdir+"/consumer_export.zip")
        with open(tempdir+"/signature", "wb") as sign_file:
            sign_file.write(signature)
    with zipfile.ZipFile(new_path, "w") as oldzip:
        oldzip.write(tempdir+"/consumer_export.zip", "/consumer_export.zip")
        oldzip.write(tempdir+"/signature", "/signature")


class Manifests(object):
    """
    Handles Red Hat manifest files.
    """

    def __init__(self, login=None, password=None):
        """
        Sets up initial configuration values
        """

        # TODO grab configuration
        # TODO setup manifest infrastructure
        self.logger = logging.getLogger("robottelo")

    def create_distributor(self, ds_name=None):
        """
        Creates the distributor with the specified name.
        """
        raise NotImplementedError()

    def attach_subscriptions(self, ds_uuid=None, quantity=None, basic=True):
        """
        Attaches all the available subscriptions with the specified quantity
        to the specified distributor uuid.
        """
        raise NotImplementedError()

    def download_manifest(self, ds_uuid=None):
        """
        Downloads a manifest.
        """
        raise NotImplementedError()

    def detach_subscriptions(self, ds_uuid=None):
        """
        Detaches all the available subscriptions of the
        distributor with the specified uuid.
        This uuid can be obtained from the fetch_manifest.
        """
        raise NotImplementedError()

    def delete_distributor(self, ds_uuid=None):
        """
        Deletes the distributor with the specified uuid.
        This uuid can be obtained from the fetch_manifest.
        """
        raise NotImplementedError()

    def fetch_manifest(self, ds_name=None, basic=True):
        """
        Fetches the manifest with the specified distributor name.
        It internally creates the distributor, attaches subscriptions,
        downloads the manifest.
        It returns the distributor/manifest path, distributor uuid and
        also the distributor name.
        """
        raise NotImplementedError()


manifest = Manifests()
