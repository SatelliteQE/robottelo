#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging
import logging.config
import os

class Base():

    logging.config.fileConfig("logging.conf")
    logger = logging.getLogger("robottelo")
    logger.setLevel(int(os.getenv('VERBOSITY', 2)))

    def execute(self, command, user='admin', password='admin'):

        shell_cmd = "katello -u %s -p %s %s -g --noheading"

        stdin, stdout, stderr = self.conn.exec_command(shell_cmd % (user, password, command))

        output = stdout.readlines()
        errors = stderr.readlines()

        self.logger.debug("".join(output))
        self.logger.debug("".join(errors))

        return output, errors
