#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a command management for Robottelo including shell command

    $ python manage.py shell
    Welcome to Robottelo Interactive shell
        Auto imported: [settings, entities, rt, ng]
    In [1]: org = entities.Organization().create()
    ... DEBUG: ... making POST resquest to...

Depends on click:
    pip install click
"""
import click
import nailgun
import code
import readline
import rlcompleter
import importlib
from robottelo.config import settings


@click.group()
def core_cmd():
    """ Core commands wrapper """
    pass


class RobotteloLoader(object):
    def __getattr__(self, item):
        return importlib.import_module('robottelo.{0}'.format(item))


@core_cmd.command()
@click.option('--ipython/--no-ipython', default=True)
def shell(ipython):
    """Runs a Python shell with Robottelo context"""
    _vars = globals()
    _vars.update(locals())
    auto_imported = {
        'settings': settings,
        'entities': nailgun.entities,
        'ng': nailgun,
        'rt': RobotteloLoader()
    }
    _vars.update(auto_imported)
    banner_msg = (
        'Welcome to Robottelo interactive shell\n'
        '\tAuto imported: {0}\n'
        '\tng is nailgun e.g: ng.client\n'
        '\trt is robottelo e.g: rt.datafactory\n'
    ).format(auto_imported.keys())
    readline.set_completer(rlcompleter.Completer(_vars).complete)
    readline.parse_and_bind('tab: complete')
    try:
        if ipython is True:
            from IPython import start_ipython
            from traitlets.config import Config
            c = Config()
            c.TerminalInteractiveShell.banner2 = banner_msg
            start_ipython(argv=[], user_ns=_vars, config=c)
        else:
            raise ImportError
    except ImportError:
        shell = code.InteractiveConsole(_vars)
        shell.interact(banner=banner_msg)


help_text = """
    Robottelo Interactive shell!
    """
manager = click.CommandCollection(help=help_text)
manager.add_source(core_cmd)

if __name__ == '__main__':
    settings.configure()
    manager()
