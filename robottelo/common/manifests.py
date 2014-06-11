# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Manifest functions
"""

import logging


class Manifests():
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
