#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import stageportal
import logging
from robottelo.common import conf


class Manifests():

    def __init__(self):

        self.api_url = conf.properties['stageportal.api']
        self.candlepin_url = conf.properties['stageportal.candlepin']
        self.portal_url = conf.properties['stageportal.customer.portal']
        self.login = conf.properties['stageportal.customer.username']
        self.password = conf.properties['stageportal.customer.password']
        self.distributor_name = conf.properties['stageportal.distributor.name']
        self.quantity = int(conf.properties['stageportal.subs.quantity'])
        self.verbosity = int(conf.properties['nosetests.verbosity'])
        self.sp = stageportal.SMPortal(api_url=self.api_url,
                                 candlepin_url=self.candlepin_url,
                                 portal_url=self.portal_url,
                                 login=self.login,
                                 password=self.password)
        logging.getLogger("python-stageportal").setLevel(logging.ERROR)
        self.logger = logging.getLogger("robottelo")

    def create_distributor(self, ds_name=None):
        """
        Creates the distributor with the specified name.
        """
        if ds_name is not None:
            self.distributor_name = ds_name
        return self.sp.create_distributor(self.distributor_name)

    def attach_subscriptions(self, ds_name=None, quantity=None):
        """
        Attaches all the available subscriptions with the specified quantity
        to the specified distributor name.
        """
        if ds_name is not None:
            self.distributor_name = ds_name
        if quantity is not None:
            self.quantity = int(quantity)
        ds_uuid = self.sp.distributor_get_uuid(self.distributor_name)
        available_subs = self.sp.distributor_available_subscriptions(ds_uuid)
        for sub in available_subs:
            if sub['quantity'] >= self.quantity:
                subs = [{'id': sub['id'],
                         'quantity': self.quantity}]
                attach_subs = self.sp.distributor_attach_subscriptions(ds_uuid,
                                                                       subs)
                if attach_subs != "<Response [200]>":
                    self.logger.error("Attaching subscription %s failed." \
                                      % sub['id'])
            else:
                self.logger.debug("Specified quantity : %s, is more than the \
                available quantity: %s" (self.quantity, sub['quantity']))
        attached_subs = self.sp.distributor_attached_subscriptions(ds_uuid)
        return attached_subs

    def fetch_manifest(self, ds_name=None):
        """
        Fetches the manifest with the specified distributor name.
        """
        if ds_name is not None:
            self.distributor_name = ds_name
        ds_uuid = self.sp.distributor_get_uuid(self.distributor_name)
        return self.sp.distributor_download_manifest(ds_uuid)

    def detach_subscriptions(self, ds_name=None):
        """
        Detaches all the available  subscriptions for the specified
        distributor.
        """
        if ds_name is not None:
            self.distributor_name = ds_name
        ds_uuid = self.sp.distributor_get_uuid(self.distributor_name)
        detach_subs = self.sp.distributor_attached_subscriptions(ds_uuid)
        detach_sub_ids = []
        for detach_sub in detach_subs:
            detach_sub_ids.append(detach_sub['id'])
        detach_subs = self.sp.distributor_detach_subscriptions(ds_uuid,
                                                               detach_sub_ids)
        if detach_subs is not None:
            detached_subs = self.sp.distributor_attached_subscriptions(ds_uuid)
            return detached_subs

    def delete_distributor(self, ds_name=None):
        """
        Deletes the distributor of the specified name.
        """
        if ds_name is not None:
            self.distributor_name = ds_name
        ds_uuid = self.sp.distributor_get_uuid(self.distributor_name)
        return self.sp.delete_distributor(ds_uuid)

manifest = Manifests()
