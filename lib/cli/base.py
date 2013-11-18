#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging
import logging.config
import os


class Base():

    try:
        logging.config.fileConfig("logging.conf")
    except Exception:
        log_format = '%(levelname)s %(module)s:%(lineno)d: %(message)s'
        logging.basicConfig(format=log_format)

    logger = logging.getLogger("robottelo")
    logger.setLevel(int(os.getenv('VERBOSITY', 2)))

    locale = os.getenv('LOCALE')
    katello_user = os.getenv('KATELLO_USER')
    katello_passwd = os.getenv('KATELLO_PASSWD')

    def execute(self, command, user=None, password=None):

        if user is None:
            user = self.katello_user
        if password is None:
            password = self.katello_passwd

        shell_cmd = "LANG=%s katello --user=%s --password=%s %s -g --noheading"

        stdin, stdout, stderr = self.conn.exec_command(
            shell_cmd % (self.locale, user, password, command))

        output = stdout.readlines()
        errors = stderr.readlines()

        self.logger.debug("".join(output))
        self.logger.debug("".join(errors))

        return output, errors
