#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.base import Base
from lib.common.helpers import csv_to_dictionary


class Host(Base):

    def __init__(self):
        self.command_base = "host"

    def delete_parameter(self, name, host_name=None, host_id=None):
        """
        Delete parameter for a host.
        """
        cmd = "host delete_parameter --name='%s'" % name

        if host_name:
            cmd += " --host-name='%s'" % host_name
        if host_id:
            cmd += " --host-id='%s'" % host_id

        stdout, stderr = self.execute(cmd)
        return False if stderr else True

    def facts(self, name=None, host_id=None, search=None, order=None,
              page=None, per_page=None):
        """
        List all fact values.
        """
        cmd = "host facts"

        if host_id:
            cmd += " --id='%s'" % host_id
        if name:
            cmd += " --name='%s'" % name

        if search:
            cmd += " --search='%s'" % search
        if order:
            cmd += " --order='%s'" % order
        if page:
            cmd += " --page='%s'" % page
        if per_page:
            cmd += " --per-page='%s'" % per_page

        stdout, stderr = self.execute(cmd)
        facts = []
        if stdout:
            facts = csv_to_dictionary(stdout)
        return facts

    def puppet_classes(self, name=None, resource_id=None, host_id=None,
                       hostgroup_id=None, environment_id=None, search=None,
                       order=None, page=None, per_page=None):
        """
        List all puppetclasses.
        """
        cmd = "host puppet_classes"

        if name:
            cmd += " --name='%s'" % name
        if resource_id:
            cmd += " --id='%s'" % resource_id

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

    def puppetrun(self, host_id=None, name=None):
        """
        Force a puppet run on the agent.
        """
        cmd = "host puppetrun"
        if host_id:
            cmd += " --id='%s'" % host_id
        if name:
            cmd += " --name='%s'" % name

        stdout, stderr = self.execute(cmd)
        return False if stderr else True

    def reports(self, name=None, host_id=None, order=None, page=None,
                per_page=None):
        """
        List all reports.
        """
        cmd = "host reports"

        if host_id:
            cmd += " --id='%s'" % host_id
        if name:
            cmd += " --name='%s'" % name

        if order:
            cmd += " --order='%s'" % order
        if page:
            cmd += " --page='%s'" % page
        if per_page:
            cmd += " --per-page='%s'" % per_page

        stdout, stderr = self.execute(cmd)
        reports = []
        if stdout:
            reports = csv_to_dictionary(stdout)
        return reports

    def set_parameter(self, name, value, host_name=None, host_id=None):
        """
        Create or update parameter for a host.
        """
        cmd = "host set_parameter --name='%s' --value='%s'" % (name, value)

        if host_name:
            cmd += " --host-name='%s'" % host_name
        if host_id:
            cmd += " --host-id='%s'" % host_id

        stdout, stderr = self.execute(cmd)
        return False if stderr else True

    def status(self, name=None, host_id=None):
        """
        Get status of host
        """
        cmd = "host status"

        if host_id:
            cmd += " --id='%s'" % host_id
        if name:
            cmd += " --name='%s'" % name

        stdout, stderr = self.execute(cmd)
        return False if stderr else True
