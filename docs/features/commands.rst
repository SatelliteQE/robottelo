Commands
========

This section explains Robottelo Management Commands.

.. contents::

Modules
-------

Robottelo uses `manage` and `click` for its management commands, the commands
are accessible via console using the :code:`$ manage`. To see a list of all available
commands run :code:`$ manage --help`.

The command manager specification is located at `robottelo/manage.yml` and
it is easy to add new commands to framework by creating new functions or
click commands and referring on `manage.yml` file.

There are commands to open an interactive shell, interact with UI browser, API and other utilities.

requisites
----------

To play with the management commands you need to install robottelo's
additional requirements which includes the `manage` library and also
is recommended to have iPython installed::

    $ cd robottelo
    $ make pyc-clean
    $ pip install ipython
    $ pip install -r -U requirements-optional.txt

shell
-----

The Interactive Shell is useful to test robottelo's functions and entities,
you can change code and all changes are automatically reloaded into shell so
no need to restart the shell or reload the modules.

If ipython is installed your shell will be opened using ipython but it is also
possible to use `--bpython`, `--ptpython` or bare `--python` as console.

To check the shell options run::

    $ manage shell --help

And to open the shell::

    $ manage shell

Assuming you have ipython installed you will see a console like:

.. code-block:: console

    (robottelo_env)[you@host robottelo]$ manage shell
    Python 2.7.11 (default, Jul  8 2016, 19:45:00)
    Type "copyright", "credits" or "license" for more information.

    IPython 5.0.0 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.

    Welcome to Robottelo Interactive shell
        Auto imported: ['rt', 'nailgun', 'settings', 'robottelo', 'ng', 'entities', 'locators']

    In [1]: rt.ssh.command('uname -r')
    2016-09-16 13:54:57 - robottelo.utils.ssh - DEBUG - Connected to [foreman-server.com]
    Out[1]: result(stdout=['3.10.0-327.el7.x86_64', ''], stderr=(0, ''), status=0)
    In [2]: exit

This is the Robottelo's interactive shell welcome screen and you can see some
most commonly used objects are `auto_imported` saving you time.

Also the `settings` object is loaded and configured, so you have a ready to use
environment to play with robottelo features.

ui browse
---------

In the subgroup `ui` you can find the `browse` command which opens the same
interactive shell but it also opens a new browser instance and gives you
the context to play with this.

The interaction with the `ui` browser is done trough the `session` object, and
the opened browser uses the configuration from your `robottelo.properties` file.

Open a new REPL connected to a browser session:

.. code-block:: console

    (robottelo_env)[you@host robottelo]$ manage ui browse
    2016-09-16 14:00:42 - robottelo.ui.browser - DEBUG - newSession:  {'desiredCapabilities': {'platform': 'ANY', 'browserName': 'chrome', 'version': '', 'chromeOptions': {'args': [], 'extensions': []}, 'javascriptEnabled': True}}

    Welcome to Robottelo Interactive shell
        Auto imported: ['rt', 'nailgun', 'settings', 'robottelo', 'ng', 'entities', 'host', 'session', 'current_browser', 'locators', 'ui_factory', 'api_factory', 'browser']

    In [1]: session.browser
    Out[1]: <robottelo.ui.browser.Chrome (session="0968e34f29e2c3208554ada58023fa4f")>

    In [2]: session.nav.go_to_users()
    2016-09-16 14:01:15 - robottelo.ui.browser - DEBUG - mouseMoveTo:  {'element': '0.8036987570003233-1'}

    In [3]: session.ui.user.click(locators.locators.users.new)
    2016-09-16 14:01:46 - robottelo.ui.browser - DEBUG - clickElement:  {'id': '0.12969267888817115-2'}

    In [4]: session.ui.user.assign_value(locators.locators.users.username, "my_username")
    2016-09-16 14:02:13 - robottelo.ui.browser - DEBUG - sendKeysToElement:  {'id': '0.12969267888817115-3', 'value': 'my_username'}

    In [5]: exit
    2016-09-16 14:05:46 - robottelo.ui.browser - DEBUG - logout
    2016-09-16 14:05:46 - robottelo.ui.browser - DEBUG - Close Browser

While you interact wth the UI using the helpers as the ones in the exemple above
you see your browser window changing interactively, if you prefer to use a docker browser
it is possible to connect via VNC or get screenshots calling :code:`session.browser.save_screenshot()`

It is also possible to open the `browse` session in specific page if you specify the entity name

.. code-block:: console

    # opens the session with browser already in users page
    (robottelo_env)[you@host robottelo]$ manage ui browse user

    # create user using factory
    In [1]:  session.ui.make_user(username="my_username")
