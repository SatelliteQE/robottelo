Quickstart
==========

This page gives you a good introduction in how to get started with ``Robottelo``.
If you haven't cloned the source code yet, then make sure to do it now:
::
    git clone git://github.com/omaciel/robottelo.git

Now, let's get started with some simple tests.

Createing new users
-------------------

Adding new users to a Katello system is pretty simple. First, add the ``username``,
``password`` and ``email`` address for the users you want to add into a ``resource``
file. Assuming you created a new ``cartoon_users.txt`` file
::
    *** Variables ***
    # Variable name     # Username      #Password   # Email
    @{cartoon_user_0}   Homer Simpson   dohh        sprinfieldguy@example.com
    @{cartoon_user_1}   Fred Flinstone  yabba       bedrock4ever@example.com

Now let's add a test file to create these users
::
    *** settings ***    *** Value ***

    Resource        resources/global.txt
    Resource        cartoon_users.txt

    Library         lib/administration.py       ${BASE_URL}    ${BROWSER}

    Test Teardown   Stop Browser

    *** Test Case ***

    Create User Homer Simpson
        Login User      @{ADMIN_USER}    @{ADMIN_PASSWD}
        Create User     @{cartoon_user_0}[0]     @{cartoon_user_0}[1]    @{cartoon_user_0}[2]
    Create User Fred Flinstone
        Login User      @{ADMIN_USER}    @{ADMIN_PASSWD}
        Create User     @{cartoon_user_1}[0]     @{cartoon_user_1}[1]    @{cartoon_user_1}[2]

Your test file contains a couple of sections: ``settings`` and ``test case``.

Settings Section
----------------
The ``settings`` section is where we import our resources and data files to be used by our tests.
You can see the ``global.txt`` file which contains data related to where our ``Katello`` server
is located, the password for the administrator account, and other useful pieces of information
that will be used by the test runner itself.

This is also where we import supporting modules that will perform the actions we want to execute,
as can be seen by the line ``Library         lib/administration.py       ${BASE_URL}    ${BROWSER}``.
The file ``administration.py`` is a ``python`` class with methods that map to actions the user
can perform in the web ui. For this example, we'll be using the ``Create User`` method.

Test Case Section
-----------------
This is where we create our tests by using the individual methods provided by the ``Library``
modules to custom build an action.
::
    Login User      @{ADMIN_USER}    @{ADMIN_PASSWD}

This individual test makes use of the ``Login User`` method provided by the ``Library`` modules
to perform the action of login into the web ui using the administrator account.
::
    Create User     @{cartoon_user_0}[0]     @{cartoon_user_0}[1]    @{cartoon_user_0}[2]

This next line passes the user's personal information to the ``Create User`` method which,
as you may have guessed, will create the user account using the web ui.

By taking advantage of the modules imported into the ``Library`` and data from ``resource``
files, we could then create a more complex test, such as creating roles and assignining them
to new or existing users
::
    Create User 1
        Login User      @{ADMIN_USER}    @{ADMIN_PASSWD}
        Create User     @{brazil_user_1}[0]     @{brazil_user_1}[1]    @{brazil_user_1}[2]
    Create Role Role1
        Login User      @{ADMIN_USER}    @{ADMIN_PASSWD}
        Create Role      ${america_admin_role_1}
        Add Permission To Role  ${america_admin_role_1}    ${scope_global}   ${permissions_organizations}   ${verb_read_organizations}   acme_read_orgs
        Add Permission To Role  ${america_admin_role_1}    ${scope_global}   ${permissions_organizations}   ${verb_delete_systems}   acme_delete_systems

