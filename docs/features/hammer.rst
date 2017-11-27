===============================================
Hammer CLI (The Foreman Command Line Interface)
===============================================

This section explains how to test hammer and add new sub commands.

.. contents::

Introduction
============

Robottelo uses ssh together with Hammer CLI to assert all features exposed
on The Foreman CommandLine interface.

The following sections contains details to write such test cases


PyToCLI
=======
.. _pytocli: https://github.com/renzon/pytocli

The lib _pytocli is used to help creating hammer commands. The base Hammer
CommandBuilder can be used to explore available option and sub-commands::

    >>> # Imporing base pacakge
    >>> from robottelo.cli.hammer_pytocli import *
    >>> # Creating a CommandBuilder instance
    >>> hammer=Hammer()
    >>> # Inspection available options
    >>> hammer.options
    ('help', 'debug', 'username', 'password', 'verbose', 'output')
    >>> # Inspection available sub commands
    >>> hammer.sub_commands
    ('organization', 'settings')
    >>> hammer.organization
    SubCommandBuilder organization: Class representing organization sub command
    >>> hammer.organization.sub_commands
    ('list',)
    >>> # Creating a command to list Organizations
    >>> hammer.organization.list
    SubCommandBuilder list: Class representing organization list sub command
    >>> # Generating the respective ssh command
    >>> str(hammer.organization.list)
    'hammer organization list'

The framework follows the fluent interface design pattern and it's useful to
 explore. Options can be added to the commands::


    >>> # Adding verbose option
    >>> hammer.verbose()
    CommandBuilder hammer: Base parent class hammer
    >>> # Checking command result
    >>> str(hammer)
    'hammer -v'
    >>> # Checcking result together with sub command
    >>> str(hammer.organization.list)
    'hammer -v organization list'

SubCommands can be used as shortcuts::

    >>> list_cmd = OrganizationListCmd()
    >>> str(list_cmd)
    'hammer organization list'

Hammer root command can be accessed using hammer attribute so extra options can
 be added on any time::

    >>> list_cmd.hammer.username('John')
    CommandBuilder hammer: Base parent class hammer
    >>> str(list_cmd)
    'hammer -u John organization list'

Adding new Sub Commands
-----------------------

Hammer has an huge list of sub commands and at some point new ones must
be added. As example let's create the infrastructure to reflect the
subcommand to list settings::

    hammer settings list

Step 1: create a subclass of HammerSubcommand::
    @Hammer.add_subcommand
    class SettingsCmd(HammerSubCommand):
        """class representing settings command"""
        name = u'settings' # this is the name of the command on CLI

This step is enough so you can generate the command from this class::

    >>> str(SettingsCmd())
    'hammer settings'
    >>> hammer.sub_commands
    ('organization', 'settings')
    >>> str(hammer.settings)
    'hammer settings'

SubCommands also has their sub-commands and the process is similar. The
only change is the decorator, which must be from the SubCommand::

    @SettingsCmd.add_subcommand
    class SettingsListCmd(SettingsSubCommand):
        """Class representing settings list command"""
        name = u'list'

This way you have the complete command::

    >>> from robottelo.cli.hammer import SettingsListCmd
    >>> str(SettingsListCmd())
    'hammer settings list'

Executing Tests against CLI using SSH
====================================

``execute`` is the main method to execute Hammer Commands against a Foreman
server.

The output will be reinforced to json and standard output will be parsed.
Be sure to have a running Foreman host and add it's settings to robottelo
.properties before running the above code::

    >>> from robottelo.config import settings
    >>> settings.configure()
    >>> cmd = OrganizationListCmd()
    >>> parsed = cmd.execute()
    2017-11-28 12:11:23 - robottelo.ssh - DEBUG - Instantiated Paramiko client 0x7fe4c97290d0
    2017-11-28 12:11:23 - robottelo.ssh - INFO - Connected to [foremanhost.com]
    2017-11-28 12:11:23 - robottelo.ssh - INFO - >>> LANG=en_US.UTF-8 hammer --output json -u username -p password organization list
    2017-11-28 12:11:26 - robottelo.ssh - INFO - <<< stdout

Finally the returned object can be inspected::

    >> from pprint import pprint
    >>> pprint(parsed)
    [{u'description': None,
      u'id': u'1',
      u'label': u'Default_Organization',
      u'name': u'Default Organization',
      u'title': u'Default Organization'}]
    >>> parsed[0]['name']
    u'Default Organization'
