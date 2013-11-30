#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from lib.common.helpers import csv_to_dictionary


class Hostgroup(Base):

    def __init__(self, conn):
        self.conn = conn

    def list(self, search=None, order=None, page=None, per_page=None):
        """
        List all hostgroups.
        """
        cmd = "hostgroup list"

        if search:
            cmd += " --search='%s'" % search
        if order:
            cmd += " --order='%s'" % order
        if page:
            cmd += " --page='%s'" % page
        if per_page:
            cmd += " --per-page='%s'" % per_page

        stdout, stderr = self.execute(cmd)

        hostgroups = []
        if stdout:
            hostgroups = csv_to_dictionary(stdout)

        return hostgroups

    def update(self, hostgroup_id, name=None, parent_id=None, environment_id=None,
               operatingsystem_id=None, architecture_id=None, medium_id=None,
               ptable_id=None, puppet_ca_proxy_id=None, subnet_id=None,
               domain_id=None, puppet_proxy_id=None):
        """
        Updates existing hostgroup.
        """
        cmd = "hostgroup update --id='%s'" % hostgroup_id

        if name:
            cmd += " --name='%s'" % name
        if parent_id:
            cmd += " --parent-id='%s'" % parent_id
        if environment_id:
            cmd += " --environment-id='%s'" % environment_id
        if operatingsystem_id:
            cmd += " --operatingsystem-id='%s'" % operatingsystem_id
        if architecture_id:
            cmd += " --architecture-id='%s'" % architecture_id
        if medium_id:
            cmd += " --medium-id='%s'" % medium_id
        if ptable_id:
            cmd += " --ptable-id='%s'" % ptable_id
        if puppet_ca_proxy_id:
            cmd += " --puppet-ca-proxy-id='%s'" % puppet_ca_proxy_id
        if subnet_id:
            cmd += " --subnet-id='%s'" % subnet_id
        if domain_id:
            cmd += " --domain-id='%s'" % domain_id
        if puppet_proxy_id:
            cmd += " --puppet-proxy-id='%s'" % puppet_proxy_id

        stdout, stderr = self.execute(cmd)
        return False if stderr else True

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

    def delete(self, hostgroup_id):
        """
        Deletes an existing hostgroup.
        """
        cmd = "hostgroup delete --id='%s'" % hostgroup_id
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

    def create(self, name, parent_id=None, environment_id=None,
               operatingsystem_id=None, architecture_id=None, medium_id=None,
               ptable_id=None, puppet_ca_proxy_id=None, subnet_id=None,
               domain_id=None, puppet_proxy_id=None):
        """
        Create hostgroup.
        """
        cmd = "hostgroup create --name='%s'" % name

        if parent_id:
            cmd += " --parent-id='%s'" % parent_id
        if environment_id:
            cmd += " --environment-id='%s'" % environment_id
        if operatingsystem_id:
            cmd += " --operatingsystem-id='%s'" % operatingsystem_id
        if architecture_id:
            cmd += " --architecture-id='%s'" % architecture_id
        if medium_id:
            cmd += " --medium-id='%s'" % medium_id
        if ptable_id:
            cmd += " --ptable-id='%s'" % ptable_id
        if puppet_ca_proxy_id:
            cmd += " --puppet-ca-proxy-id='%s'" % puppet_ca_proxy_id
        if subnet_id:
            cmd += " --subnet-id='%s'" % subnet_id
        if domain_id:
            cmd += " --domain-id='%s'" % domain_id
        if puppet_proxy_id:
            cmd += " --puppet-proxy-id='%s'" % puppet_proxy_id

        stdout, stderr = self.execute(cmd)
        return False if stderr else True

    def info(self, hostgroup_id):
        """
        Show a hostgroup.
        """
        cmd = "hostgroup info --id='%s'" % hostgroup_id
        stdout, stderr = self.execute(cmd)

        hostgroup = []
        if stdout:
            hostgroup = csv_to_dictionary(stdout)
        return hostgroup

    def exists(self, name):
        """
        Returns True or False depending whether the hostgroup exists
        in the system or not.
        """
        hostgroups = self.list()
        return name in [hostgroup['Name'] for hostgroup in hostgroups]

    def hostgroup(self, name):
        """
        Search for hostgrpup by name.
        """
        hostgroups = self.list()
        match = [
            hostgroup for hostgroup in hostgroups if name in hostgroup['Name']
        ]

        if match:
            match = match[0]

        return match
