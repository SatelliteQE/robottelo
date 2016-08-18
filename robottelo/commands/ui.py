# coding: utf-8
"""
This module contains commands to interact with UI via console

Commands included:

Browse
------

A command to open a browser session using the configured preferences from
`robottelo.properties` file and provide an interactive shell to play with
browser session::

    $ manage ui browse <entity>
    >>> session.nav.go_to_entity()
    >>> session.ui.make_user(username='my_username')

Please take a look at :doc:`commands package </features/commands>` page
in documentation for more details.

"""
import click
import import_string

from functools import partial
from inspect import getmembers
from manage.cli import create_shell
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import UI_CRUD
from robottelo.helpers import Storage
from robottelo.ui.browser import browser as selenium_browser
from robottelo.ui.browser import DockerBrowser
from robottelo.ui import factory as ui_factory
from robottelo.ui.session import Session


def _get_browser(browser=None):
    """Gets a new instance of a browser to interact"""

    browser = browser or settings.browser
    if browser == 'docker':
        _docker_browser = DockerBrowser()
        _docker_browser.start()
        _browser = _docker_browser.webdriver
    elif browser == "selenium":
        _browser = selenium_browser()
    else:
        raise NotImplementedError(
            "this shell only supports docker and selenium")

    _browser.maximize_window()
    _browser.get(settings.server.get_url())
    return _browser


def _import_ui_crud():
    """Imports all UI crud related classes to shell scope"""
    # FIXME: get all subclasses of robotello.ui.base.Base automatically
    base_module = "robottelo.ui.{0}"
    return {
        name.split('.')[-1]: import_string(base_module.format(name))
        for name in UI_CRUD
    }


@click.command()
@click.option('--host', required=False, default=None,
              help="satellite host name e.g:'foo.bar.com'")
@click.option('--browser', required=False, default=None,
              help='selenium or docker (defaults to properties file)')
@click.argument('entity', required=False, default=None)
def browse(entity, browser, host):
    """Opens a page in defined browser for interaction:\n
    All parameters defaults to what is in robottelo.properties file.\n
        example: $ manage ui browse activationkey\n
                 Opens a browser in ActivationKey scope and gives you
                 interactive shell to play with the page\n
    """
    settings.configure()
    if host:
        settings.server.hostname = host
    current_browser = _get_browser(browser)
    with Session(current_browser) as session:  # noqa

        ui_crud = _import_ui_crud()
        # Make all UI CRUD entities available in a dict
        # each entity initialized with current_browser instance
        ui_entities = {
            name.lower(): crud_class(current_browser)
            for name, crud_class in ui_crud.items()
        }
        if entity:
            # if entity name specified navigate to the page
            # example: manage ui browse user
            ui_entities[entity.lower()].navigate_to_entity()

        # gets all functions from ui.factory module which starts with 'make_'
        ui_factory_members = getmembers(
            ui_factory,
            lambda i: callable(i) and i.__name__.startswith('make')
        )
        # Usually we need to pass the `session` as 1st argument
        # e.g `make_user(session, username='...')`
        # using `partial` we make session the default 1st argument
        # it allows the use as: `make_user(username='...')
        # and `session` is implicit there.
        ui_factory_functions = {
            name: partial(function, session=session)
            for name, function in ui_factory_members
        }

        # now we "inject" the factories and entities under `session.ui`
        session.ui = Storage(ui_entities, ui_factory_functions)

        # The same for nailgun.entities.* under `session.api`
        session.api = Storage(dict(getmembers(entities)))

        def close():
            """Hook to close the session and browser atexit it also flushes
            the session history content to the specified file
            """
            session.close()
            # FIXME: if --out=/path/to/file should save session history
            # see ipython.readthedocs.io/en/stable/config/options/terminal.html

        extra_vars = {
            'session': session,
            'browser': current_browser,
            'current_browser': current_browser,
            'host': settings.server.hostname,
            'api_factory': entities,
            'ui_factory': ui_factory
        }

        create_shell('ipython', extra_vars=extra_vars, exit_hooks=[close])
