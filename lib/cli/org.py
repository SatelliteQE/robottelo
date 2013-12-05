#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from itertools import izip
from lib.common.helpers import generate_name

FIELDS = ['id', 'name', 'description', 'default service level',
          'available service levels', 'default system info keys']


class Org(Base):

    def __init__(self):
        self.command_base = "org"

    def attach_all_systems(self):
        pass

    def create(self, name=None, label=None, description=None):
        cmd = "org create --name='%s' --label='%s'"

        if name is None:
            name = generate_name()
        if description is None:
            description = "Automatically generated"

        cmd = cmd % (name, label, description)

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def default_info(self):
        pass

    def delete(self, name):
        cmd = "org delete --name='%s'"

        stdout, stderr = self.execute(cmd % name)

        return False if stderr else True

    def info(self, name):
        cmd = "org info --name='%s'"

        org = {}

        stdout, stderr = self.execute(cmd % name)

        if stdout:
            org = dict(izip(FIELDS, "".join(stdout).split()))

        return org

    def list(self):
        cmd = "org list"

        orgs = []

        stdout, stderr = self.execute(cmd)

        if stdout:
            for entry in stdout:
                orgs.append(dict(izip(FIELDS, "".join(entry).split())))

        return orgs

    def subscriptions(self):
        pass

    def uebercert(self):
        pass

    def update(self, name, description=None, service_level=None):
        cmd = "org update --name='%s'" % name

        if description:
            cmd += " --description='%s'" % description
        if service_level:
            cmd += " --servicelevel='%s'" % service_level

        stdout, stderr = self.execute(cmd)

        return False if stderr else True
