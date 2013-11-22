#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging.config
from lib.common import conf


class Base():

    try:
        logging.config.fileConfig("logging.conf")
    except Exception:
        log_format = '%(levelname)s %(module)s:%(lineno)d: %(message)s'
        logging.basicConfig(format=log_format)

    logger = logging.getLogger("robottelo")
    logger.setLevel(int(conf.properties['main.verbosity']))

    locale = conf.properties['main.locale']
    katello_user = conf.properties['foreman.admin.username']
    katello_passwd = conf.properties['foreman.admin.password']

    def execute(self, command, user=None, password=None):

        if user is None:
            user = self.katello_user
        if password is None:
            password = self.katello_passwd

        shell_cmd = "LANG=%s hammer -u %s -p %s --csv %s"

        stdin, stdout, stderr = self.conn.exec_command(
            shell_cmd % (self.locale, user, password, command))

        output = stdout.readlines()
        errors = stderr.readlines()

        self.logger.debug(shell_cmd % (self.locale, user, password, command))
        self.logger.debug("".join(output))
        self.logger.debug("".join(errors))

        return output, errors
