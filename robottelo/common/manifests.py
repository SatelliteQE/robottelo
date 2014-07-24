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


def edit_in_zip(zipfname, file_edit_functions):
    tempdir = tempfile.mkdtemp()
    try:
        tempname = os.path.join(tempdir, 'new.zip')
        with zipfile.ZipFile(zipfname, 'r') as zipread:
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
        shutil.move(tempname, zipfname)
    finally:
        shutil.rmtree(tempdir)


def edit_consumer(data):
    content_dict = json.loads(data)
    content_dict['uuid'] = str(uuid.uuid1())
    return json.dumps(content_dict)


def clone(oldpath, newpath):
    shutil.copy(oldpath, newpath)
    tempdir = tempfile.mkdtemp()
    with zipfile.ZipFile(newpath) as oldzip:
        oldzip.extractall(tempdir)
        edit_in_zip(tempdir+"/consumer_export.zip",
                    {"/export/consumer.json": edit_consumer})
    with zipfile.ZipFile(newpath, "w") as oldzip:
        oldzip.write(tempdir+"/consumer_export.zip", "/consumer_export.zip")


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
