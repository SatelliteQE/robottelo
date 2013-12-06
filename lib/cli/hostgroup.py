#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.base import Base
from lib.common.helpers import csv_to_dictionary


class Hostgroup(Base):

    def __init__(self):
        self.command_base = "hostgroup"

    def delete_parameter(self, hostgroup_id, name):
        """
        Delete parameter for a hostgroup.
        """
        cmd = "hostgroup delete_parameter --hostgroup-id='%s' --name='%s'" % \
              (hostgroup_id, name)
        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def set_parameter(self, hostgroup_id, name, value):
        """
        Create or update parameter for a hostgroup.
        """
        cmd = "hostgroup set_parameter --hostgroup-id='%s'" % hostgroup_id
        cmd += " --name='%s' --value='%s'" % (name, value)

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def puppet_classes(self, hg_id, host_id=None, hostgroup_id=None,
                       environment_id=None, search=None, order=None, page=None,
                       per_page=None):
        """
        List all puppetclasses.
        """
        cmd = "hostgroup puppet_classes --id='%s'" % hg_id

        if host_id:
            cmd += " --host-id='%s'" % host_id
        if hostgroup_id:
            cmd += " --hostgroup-id='%s'" % hostgroup_id
        if environment_id:
            cmd += " --environment-id='%s'" % environment_id
        if search:
            cmd += " --search='%s'" % search
        if order:
            cmd += " --order='%s'" % order
        if page:
            cmd += " --page='%s'" % page
        if per_page:
            cmd += " --per-page='%s'" % per_page

        stdout, stderr = self.execute(cmd)

        puppet_classes = []

        if stdout:
            puppet_classes = csv_to_dictionary(stdout)
        return puppet_classes
