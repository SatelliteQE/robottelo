# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Manifest functions
"""

import zipfile
import tempfile
import json
import uuid
import shutil
import os
import requests
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from robottelo.common import conf
from robottelo.common import ssh


def get_tempfile():
    """
    Generates temporary file with mkstemp,
    closes the handle, and returns the path to temporary file.
    """
    fd, tempname = tempfile.mkstemp()
    os.fdopen(fd).close()
    return tempname


def retrieve(url):
    """
    Downloads content of the url and saves it to temporary file.
    Then returns the path to the temporary file.
    """
    response = requests.get(url)
    fd, tempname = tempfile.mkstemp()
    with os.fdopen(fd, "wb") as temp_file:
        temp_file.write(response.content)
    return tempname


def download_signing_key():
    """
    Downloads the configured key file to a temporary file and returns the path.
    """
    return retrieve(conf.properties['main.manifest.key_url'])


def download_manifest_template():
    """
    Downloads the configured manifest file to serve as a template and
    returns the path.
    """
    return retrieve(conf.properties['main.manifest.fake_url'])


def install_cert_on_server():
    """
    Downloads specified cert-file to the servers candlepin cert repository.
    Then it restarts tomcat.
    """
    ssh.command('wget -P /etc/candlepin/certs/upstream/ {0}'.format(
        conf.properties['main.manifest.cert_url']))
    # Problem with difference between sat 6 and 7
    # Need to account for different names of tomcat
    ssh.command('service tomcat restart')
    ssh.command('service tomcat6 restart')


def sign(key_file, file_to_sign):
    """
    Reads the rsa key file and then proceeds to create signed sha256
    hash of the data in the file according to PKCS1 1.5 standard.

    Returns binary signature data.
    """
    with open(key_file) as handle:
        signature = PKCS1_v1_5.new(RSA.importKey(handle.read()))
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
    """
    Takes the string-data of the consumer file and updates with new uuid
    """
    content_dict = json.loads(data)
    content_dict['uuid'] = unicode(uuid.uuid1())
    return json.dumps(content_dict)


def clone(key_path, old_path):
    """
    Taking a manifest on oldpath, changes the uuid in consumer.json and resigns
    it with an RSA key. When accompanying certificate is installed on the
    candlepin server, it allows us to quickly create uploadable
    copies of the original manifest.
    """
    new_path = get_tempfile()
    shutil.copy(old_path, new_path)
    tempdir = tempfile.mkdtemp()
    with zipfile.ZipFile(new_path) as oldzip:
        oldzip.extractall(tempdir)
    edit_in_zip(
        tempdir+"/consumer_export.zip",
        {"consumer.json": edit_consumer}
    )
    signature = sign(key_path, tempdir+"/consumer_export.zip")
    with open(tempdir+"/signature", "wb") as sign_file:
        sign_file.write(signature)
    with zipfile.ZipFile(new_path, "w") as oldzip:
        oldzip.write(tempdir+"/consumer_export.zip", "/consumer_export.zip")
        oldzip.write(tempdir+"/signature", "/signature")
    return new_path
