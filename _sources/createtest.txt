Creating A New Test Case
========================

Before Proceeding
-----------------
The process of creating a test case file follows the same exact steps and syntax described in the Robot `Framework User Guide <http://robotframework.googlecode.com/hg/doc/userguide/RobotFrameworkUserGuide.html?r=2.7.1>`_. All the test files included in the ``tests`` directory use at least ``2 spaces`` to separate ``keywords`` and ``variables`` from each other, but one can use any one of the formats currently supported by the framework. For an overview on how to `create a test case <http://robotframework.googlecode.com/hg/doc/userguide/RobotFrameworkUserGuide.html?r=2.7.1#creating-test-data>`_. As this is not a tutorial on how to create test cases for the Robot Framework, I strongly recommend that you familiarize yourself with this process by reading their recommendation before proceeding.

Importing Resources
-------------------
``Resource`` files is how we provide vital information and data to the test cases that we want to run. These files are currently located inside the ``resources`` directory, and with the exception of the ``global.txt`` file, which provides generic information for the test suite, they contain data that is used by the test cases themselves. Let's take a look at the ``cartoon_users.txt`` file for instance:

::

    *** Variables ***
    # Variable name     # Username      #Password   # Email
    @{cartoon_user_0}   Homer_Simpson   dohh        sprinfieldguy@example.com
    @{cartoon_user_1}   Fred_Flinstone  yabba       bedrock4ever@example.com

The variable ``@{cartoon_user_0}`` contains three pieces of information about a single user and can be used throughout the entire test suite. In order to add a new user to your tests, simply add a new row to this file with the corresponding information. Once you have your data, import it into your test file ``my_test.txt``:

::

    *** settings ***    *** Value ***

    Resource        resources/global.txt
    Resource        resources/my_test.txt

``Important``: Note that the path to the ``resources`` directory has to be relative to where your test file live.

Importing Library Modules
-------------------------
``Library`` modules are python modules that provide the necessary actions and methods to access parts of the web ui and to literally navigate through the application using ``Selenium`` and the ``Firefox`` web browser. As most of the actions in ``Katello`` require that the user is logged and authenticated, the ``login.py`` module is required for all of your tests. Library modules are imported as shown below:

::

    Library         lib/login.py    ${BASE_URL}    ${BROWSER}

The arguments ${BASE_URL} and ${BROWSER} are passed to this module, because login is actually a class that expects two arguments in its constructor, but classes that don't require arguments in their constructor can be imported as shown:

::

    Library         lib/administration.py

``Important``: Note that the path to the directory containing your library modules has to be relative to where your test file live.

Writing Test Cases
==================
To write your test cases then, all you have to do is give it a name and then match the methods included in your library with the variables provided by your resource files to map the action you want to perform in the application. ``Remember`` to perform the login step first as it is a required step to use the application! So a test that logs the administrator user and then creates the Homer_Simpson user would look like this:

::

    Create User Homer Simpson
        Login User      @{ADMIN_USER}    @{ADMIN_PASSWD}
        Create User     @{cartoon_user_0}[0]     @{cartoon_user_0}[1]    @{cartoon_user_0}[2]
        Teardown        Stop Browser

As you may have guessed, both ``@{ADMIN_USER}`` and ``@{ADMIN_PASSWD}`` are variables that are passed to the test (in this particular case by the ``global.txt`` file, but you can also pass them via the command line). The administrator user logs in and then the new user is created by calling the ``Create User`` method and passing the user's name, password and email as its arguments. The last step is to close the web browser via the ``Stop Browser`` method. It is possible to create default actions for the ``setup`` and/or ``teardown`` steps for individual or all tests, as well as for the entire suite. So if all the test cases in your file will be performed by the administrator user, then it may make more sense to do the following:

::

    *** settings ***    *** Value ***

    Resource        resources/global.txt
    Resource        resources/my_test.txt
    Library         lib/login.py    ${BASE_URL}    ${BROWSER}
    Library         lib/administration.py

    Test Setup      Login User      @{ADMIN_USER}    @{ADMIN_PASSWD}
    Test Teardown   Stop Browser

    *** Test Case ***

    Create User Homer Simpson
        Create User     @{cartoon_user_0}[0]     @{cartoon_user_0}[1]    @{cartoon_user_0}[2]
    Create User Fred Flinstone
        Create User     @{cartoon_user_1}[0]     @{cartoon_user_1}[1]    @{cartoon_user_1}[2]
