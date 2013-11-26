#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from itertools import izip
from lib.common.helpers import generate_name

FIELDS = ['name', 'id']

class Org(Base):

    def __init__(self, conn):
        self.conn = conn

    def attach_all_systems(self):
        pass

    def create(self, name=None):
        cmd = "organization create --name='%s'"
        if name is None:
            name = generate_name()

        cmd = cmd % (name)
        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def default_info(self):
        pass

    def delete(self, name):
        cmd = "organization delete --name='%s'"

        stdout, stderr = self.execute(cmd % name)

        return False if stderr else True

    def info(self, name):
        cmd = "organization info --name='%s'"

        org = {}

        stdout, stderr = self.execute(cmd % name)

        if stdout:
            org = dict(izip(FIELDS, "".join(stdout).split()))

        return org

    def list(self):
        cmd = "organization list"

        orgs = []

        stdout, stderr = self.execute(cmd)

        if stdout:
            for entry in stdout:
                orgs.append(dict(izip(FIELDS, "".join(entry).split())))

        return orgs

    def info(self, org_name):
        """
        gets info about an organization
        """
        cmd = "organization info --name='%s'"

        org = {}

        stdout, stderr = self.execute(cmd % org_name)

        if stdout:
            org = csv_to_dictionary(stdout)

        return org

    def exists(self, org_name):
        """
        Returns whether or not org exists.
        """
        org_data = []
        organizations = self.list()
        for org in organizations:
            for val in org.values():
                org_data.append(val.split(',')[-1])
        return org_name in org_data
 
    def subscriptions(self):
        pass

    def uebercert(self):
        pass

    # Is this deprecated (for now?)
    def update(self, name, description=None, service_level=None):
        cmd = "organization update --name='%s'" % name

        if description:
            cmd += " --description='%s'" % description
        if service_level:
            cmd += " --servicelevel='%s'" % service_level

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

