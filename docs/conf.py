"""Sphinx documentation generator configuration file.

The full set of configuration options is listed on the Sphinx website:
http://sphinx-doc.org/config.html

"""
import os
import sys


def skip_data(app, what, name, obj, skip, options):
    """Skip double generating docs for robottelo.decorators.func_shared.shared"""
    if what == 'function' and name == 'robottelo.decorators.func_shared.shared':
        return True
    return None


def setup(app):
    app.connect("autoapi-skip-member", skip_data)


# Add the Robottelo root directory to the system path. This allows references
# such as :mod:`robottelo` to be processed correctly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

# Project Information ---------------------------------------------------------

project = 'Robottelo'
copyright = '2012, Og Maciel <omaciel@redhat.com>'

# `version` should be a short X.Y version, and `release` should be a full
# version string. Robottelo has thus far had little use for versions, which is
# why it is still at 0.0.1.
version = '0.0.1'
release = version

# General configuration -------------------------------------------------------

extensions = ['autoapi.extension', 'sphinx.ext.autodoc', 'sphinx.ext.viewcode']
autoapi_dirs = ['../robottelo']
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build', 'pytest/*']
nitpicky = True
nitpick_ignore = [
    ('py:class', 'bool'),
    ('py:class', 'callable'),
    ('py:class', 'dict'),
    ('py:class', 'Exception'),
    ('py:class', 'int'),
    ('py:class', 'list'),
    ('py:class', 'object'),
    ('py:class', 'set'),
    ('py:class', 'str'),
    ('py:class', 'tuple'),
    ('py:class', 'broker.hosts.Host'),
    ('py:class', 'json.JSONEncoder'),
    ('py:class', 'nailgun.entities.ActivationKey'),
    ('py:class', 'nailgun.entities.Organization'),
    ('py:class', 'nailgun.entities.Environment'),
    ('py:class', 'nailgun.entities.Product'),
    ('py:class', 'nailgun.entities.Role'),
    ('py:class', 'nailgun.entities.Repository'),
    ('py:class', 'paramiko.SSHClient'),
    ('py:mod', 'robottelo.cli.template_sync'),
    ('py:class', 'unittest2.case.TestCase'),
    ('py:class', 'unittest2.TestCase'),
    ('py:class', 'wrapt.CallableObjectProxy'),
    ('py:mod', 'tests'),
    ('py:mod', 'tests.foreman'),
    ('py:mod', 'tests.foreman.cli'),
]
autodoc_default_options = {'members': None, 'undoc-members': None}

# Format-Specific Options -----------------------------------------------------

htmlhelp_basename = 'Robottelodoc'
latex_documents = [
    (
        'index',
        'Robottelo.tex',
        'Robottelo Documentation',
        'Og Maciel \\textless{}omaciel@redhat.com\\textgreater{}',
        'manual',
    )
]
man_pages = [
    ('index', 'robottelo', 'Robottelo Documentation', ['Og Maciel <omaciel@redhat.com>'], 1)
]
texinfo_documents = [
    (
        'index',
        'Robottelo',
        'Robottelo Documentation',
        'Og Maciel <omaciel@redhat.com>',
        'Robottelo',
        'One line description of project.',
        'Miscellaneous',
    )
]
epub_title = 'Robottelo'
epub_author = 'Og Maciel <omaciel@redhat.com>'
epub_publisher = 'Og Maciel <omaciel@redhat.com>'
epub_copyright = '2012, Og Maciel <omaciel@redhat.com>'
