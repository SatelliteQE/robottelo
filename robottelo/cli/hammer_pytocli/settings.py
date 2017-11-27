# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pytocli import Option, SingleValueOption

from robottelo.cli.hammer_pytocli.base import Hammer, HammerSubCommand


@Hammer.add_subcommand
class SettingsCmd(HammerSubCommand):
    """class representing settings command"""
    name = u'settings'


@SettingsCmd.add_subcommand
class SettingsListCmd(HammerSubCommand):
    """Class representing settings list command"""
    name = u'list'


@SettingsCmd.add_subcommand
class SettingsSetCmd(HammerSubCommand):
    """Class representing settings list command"""
    name = u'set'
    name_option = Option(SingleValueOption, u'--name')
    value = Option(SingleValueOption, u'--value')
