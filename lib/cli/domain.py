#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base


class Domain(Base):

    def __init__(self, conn):
        self.conn = conn
        self.command_base = "domain"

    def delete_parameter(self, name, domain_name=None, domain_id=None):
        """
        Delete parameter for a domain.
        """
        cmd = "delete_parameter --name='%s'" % name

        if domain_id:
            cmd += " --domain-id='%s'" % domain_id
        if domain_name:
            cmd += " --domain-name='%s'" % domain_name

        stdout, stderr = self.execute(cmd)
        return False if stderr else True

    def set_parameter(self, name, value, domain_name=None, domain_id=None):
        """
        Create or update parameter for a domain.
        """
        cmd = "set_parameter --name='%s' --value='%s'" % (name, value)

        if domain_id:
            cmd += " --domain-id='%s'" % domain_id
        if domain_name:
            cmd += " --domain-name='%s'" % domain_name

        stdout, stderr = self.execute(cmd)
        return False if stderr else True
