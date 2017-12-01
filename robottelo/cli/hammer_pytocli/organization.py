# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from robottelo.cli.hammer_pytocli.base import Hammer, HammerSubCommand


@Hammer.add_subcommand
class OrganizationCmd(HammerSubCommand):
    """Class representing organization sub command"""
    name = u'organization'
    # list = SubCommand(OrganizationListCmd)


@OrganizationCmd.add_subcommand
class OrganizationListCmd(HammerSubCommand):
    """Class representing organization list sub command"""
    name = u'list'
