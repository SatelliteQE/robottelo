# -*- encoding: utf-8 -*-
"""
Implements Manifest functions
"""

import json
import os
import requests
import shutil
import tempfile
import uuid
import zipfile

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from robottelo.config import conf


def get_tempfile():
    """Creates a temporary file.

    Generates temporary file with mkstemp,
    closes the handle, and returns the path to temporary file.

    """
    fd, tempname = tempfile.mkstemp()
    os.fdopen(fd).close()
    return tempname


def retrieve(url):
    """Downloads contents of a URL.

    Downloads content of the url and saves it to temporary file.
    Then returns the path to the temporary file.

    """
    response = requests.get(url)
    fd, tempname = tempfile.mkstemp()
    with os.fdopen(fd, "wb") as temp_file:
        temp_file.write(response.content)
    return tempname


def download_signing_key():
    """ Private key to Sign a modified manifest.

    Downloads the configured key file to a temporary file and returns the path.

    """
    return retrieve(conf.properties['main.manifest.key_url'])


def download_manifest_template():
    """ Manifest template used for cloning.

    Downloads the configured manifest file to serve as a template and
    returns the path.

    """
    return retrieve(conf.properties['main.manifest.fake_url'])


def sign(key_file, file_to_sign):
    """Performs the signing of the modified manifest file.

    Reads the rsa key file and then proceeds to create signed sha256
    hash of the data in the file according to PKCS1 1.5 standard.

    :param str key_file: The private key used to sign.
    :param str file_to_sign: The file name to sign.
    :return:  Returns binary signature data.

    """
    with open(key_file) as handle:
        signature = PKCS1_v1_5.new(RSA.importKey(handle.read()))
    with open(file_to_sign, "rb") as data:
        digest = SHA256.new(data.read())
    return signature.sign(digest)


def edit_in_zip(zip_file, file_edit_functions):
    """Performs the actual editing.

    Reads every file in the zip, and for every path in file_edit_functions
    dictionary it applies the relevant function on the contents of the file
    and saves it with new content.

    For example if you had zipfile /tmp/test.zip containing files small.txt,
    filler.txt and large.txt and you'd want small.txt contain 1 and large.txt
    contain 1000, you would call

    edit_in_zip("/tmp/test.zip",
        {'small.txt': lambda x: "1", 'large.txt': lambda x: "1000"})

    :param str zip_file: The zip file to edit.
    :param dict file_edit_functions: Files & Functions are the key value pairs.
    :return: None

    """
    tempdir = tempfile.mkdtemp()
    tempname = get_tempfile()

    try:
        with zipfile.ZipFile(zip_file, 'r') as zipread:
            zipread.extractall(tempdir)
        for base, _, files in os.walk(tempdir):
            for ifile in files:
                if ifile in file_edit_functions:
                    file_name = os.path.join(base, ifile)
                    data = None
                    with open(file_name) as file_to_change:
                        content = file_to_change.read()
                        data = file_edit_functions[ifile](
                            content
                        )
                    with open(file_name, 'w') as file_to_change:
                        file_to_change.write(data)
        with zipfile.ZipFile(tempname, 'w') as zipwrite:
            baselen = len(tempdir)
            for base, _, files in os.walk(tempdir):
                for ifile in files:
                    file_name_zip = os.path.join(base, ifile)[baselen:]
                    file_name = os.path.join(tempdir, file_name_zip[1:])
                    zipwrite.write(file_name, file_name_zip)
        shutil.move(tempname, zip_file)
    finally:
        shutil.rmtree(tempdir)


def edit_consumer(data):
    """Takes the string-data of the consumer file and updates with new UUID.

    :param str data: Takes in the consumer file name.
    :return: returns the json with new UUID.
    :rtype: str

    """
    content_dict = json.loads(data)
    content_dict['uuid'] = unicode(uuid.uuid1())
    return json.dumps(content_dict)


def clone(key_path=None, old_path=None):
    """Clones a RedHat-manifest file.

    Taking a manifest on oldpath, changes the uuid in consumer.json and resigns
    it with an RSA key. When accompanying certificate is installed on the
    candlepin server, it allows us to quickly create uploadable
    copies of the original manifest.

    :param str key_path: This is the private-key to sign the redhat-manifest.
    :param str old_path: This is the path of the original redhat-manifest.
    :return: Return the path to the cloned redhat-manifest file.
    :rtype: str

    """
    tempdir = tempfile.mkdtemp()
    consumer_zip_file = os.path.join(tempdir, "consumer_export.zip")
    if key_path is None:
        key_path = download_signing_key()
    if old_path is None:
        old_path = download_manifest_template()
    new_path = get_tempfile()
    shutil.copy(old_path, new_path)
    with zipfile.ZipFile(new_path) as oldzip:
        oldzip.extractall(tempdir)
    edit_in_zip(consumer_zip_file, {"consumer.json": edit_consumer})
    signature = sign(key_path, consumer_zip_file)
    with open(os.path.join(tempdir, "signature"), "wb") as sign_file:
        sign_file.write(signature)
    with zipfile.ZipFile(new_path, "w") as oldzip:
        oldzip.write(consumer_zip_file, "/consumer_export.zip")
        oldzip.write(os.path.join(tempdir, "signature"), "/signature")
    return new_path
