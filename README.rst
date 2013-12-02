Robottelo
=========
This is an automation test suite for `The Foreman <http://theforeman.org/>`_ project.

My goal is to design a `keyword <http://en.wikipedia.org/wiki/Keyword-driven_testing>`_, `data <http://en.wikipedia.org/wiki/Data-driven_testing>`_ driven suite that can be used in a continuous integration environment.

Quickstart
==========

This page gives you a good introduction in how to get started with ``Robottelo``. For more information, please read the `documentation <http://robottelo.readthedocs.org/en/latest/>`_.

Requirements:
-------------
1) If you haven't cloned the source code yet, then make sure to do it now:

::

    git clone git://github.com/omaciel/robottelo.git

2) Pre-requisites 
a) Consider using virtual-env with system-site-packages
Example:-  virtualenv --system-site-packages robottelo
b) Install locally modules in virtual-env using 'pip install -I'
rest will be picked from system site-packages.
Example:- pip install -I boto


3) Then, run **sudo pip install -r ./requirements.txt** from the root of the project to have all dependencies automatically installed.

4)You may require the below packages/software installed 
a) Consider running 'yum groupinstall "Development Tools"' 
   for fedora/RHEL or Development packages if installing the below
   modules via pip for your OS.
b) 'yum install python-rhsm' for fedora/RHEL  (would require candlepin-stage.pem & redhat-uep.pem 
                                               certs at /etc/rhsm/ca if installing via pip)
c) m2crypto (may require all the below steps, pip install m2crypto --no-clean for fedora
                                              cd /venv/build/M2Crypto
                                              chmod u+x fedora_setup.sh
                                              ./fedora_setup.sh build
                                              ./fedora_setup.sh install)
d) 'yum install rpm-python' for fedora/RHEL  (had no success with pip, I used fedora-package, found the recommended way to use is only via
                                              system-site-packages option for virtual-env)
f) 'yum install swig' for fedora/RHEL 

Running the test
----------------
Assuming you have already installed and configured **The Foreman**, the simplest way to execute tests is to use the included **robottelo_runner** script. First, make sure to copy the **robottelo.properties.sample** file and save it as **robottelo.properties**. Next, edit the file and update the attributes to match your existing configuration, and run your tests:

::

    python robottelo_runner.py --tests tests.ui.test_Login

Multiple tests can also be invoked:

::

    python robottelo_runner.py --tests tests.ui.test_Login --tests tests.ui.test_Organization

Running individual tests from a test suite from the command line:

::

    python robottelo_runner.py --tests tests.ui.test_Login.test_successful_login

You can also run tests directly using either **unittest** or **nosetests** provided you pass all the expected arguments:

::

    KATELLO_HOST=www.example.com PROJECT=katello DRIVER=firefox python -m unittest tests.ui.test_Login.test_successful_login

or

::

    KATELLO_HOST=www.example.com PROJECT=katello DRIVER=firefox nosetests tests.ui.test_Login.test_successful_login

Known Issues
============

Author
------

This software is developed by:
`Og Maciel <http://www.ogmaciel.com>`_.
