"""Sphinx documentation generator configuration file.

The full set of configuration options is listed on the Sphinx website:
http://sphinx-doc.org/config.html

"""
import sys
import os
# pylint:disable=invalid-name

# Add the Robottelo root directory to the system path. This allows references
# such as :mod:`robottelo` to be processed correctly.
sys.path.insert(
    0,
    os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir
    ))
)

# Project Information ---------------------------------------------------------

project = u'Robottelo'
copyright = u'2012, Og Maciel <omaciel@redhat.com>'  # pylint:disable=W0622

# `version` should be a short X.Y version, and `release` should be a full
# version string. Robottelo has thus far had little use for versions, which is
# why it is still at 0.0.1.
version = '0.0.1'
release = version

# General configuration -------------------------------------------------------

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build']
nitpicky = True
nitpick_ignore = [
    ('py:obj', 'bool'),
    ('py:obj', 'dict'),
    ('py:obj', 'int'),
    ('py:obj', 'sequence'),
    ('py:obj', 'str'),
    ('py:obj', 'tuple'),
]
autodoc_default_flags = ['members', 'undoc-members']

# Format-Specific Options -----------------------------------------------------

htmlhelp_basename = 'Robottelodoc'
latex_documents = [(
    'index',
    'Robottelo.tex',
    u'Robottelo Documentation',
    u'Og Maciel \\textless{}omaciel@redhat.com\\textgreater{}',
    'manual'
)]
man_pages = [(
    'index',
    'robottelo',
    u'Robottelo Documentation',
    [u'Og Maciel <omaciel@redhat.com>'],
    1
)]
texinfo_documents = [(
    'index',
    'Robottelo',
    u'Robottelo Documentation',
    u'Og Maciel <omaciel@redhat.com>',
    'Robottelo',
    'One line description of project.',
    'Miscellaneous'
)]
epub_title = u'Robottelo'
epub_author = u'Og Maciel <omaciel@redhat.com>'
epub_publisher = u'Og Maciel <omaciel@redhat.com>'
epub_copyright = u'2012, Og Maciel <omaciel@redhat.com>'

# -- Monkey patch ddt.data ----------------------------------------------------

# Monkey patch ddt.data and robottelo's ddt.data wrapper, preventing the
# decorators from generating new test methods. Without this monkey patch,
# Sphinx might document the following methods:
#
# * test_something_1_some_value
# * test_something_2_another_value
# * test_something_3_yet_another_value
#
# But with this monkey patch, Sphinx will document only one test method:
#
# * test_something
#
# As a result, the API documentation is much more concise.

import ddt  # noqa
import robottelo.decorators  # noqa pylint:disable=import-error
# robttelo.common.decorators can only be imported if the `sys.path.insert` at
# the top of this document is executed. pylint tries to be a static code
# analyzer, so that does not happen, and it therefore cannot find this module.


def monkey_data(*values):
    """Monkey patch function for ddt.data

    This function bypasses ddt.data functionality and allow Sphinx generates
    cleaner docs

    """
    # It's OK that the ``values`` argument is OK. This function just needs to
    # match the signature of ``ddt.data``.
    # pylint:disable=unused-argument
    return lambda func: func

# Cache the robottelo wrapper docstring
robottelo_data_docstring = robottelo.decorators.data.__doc__

# Do the monkey patch on ddt.data and robottelo wrapper
ddt.data = robottelo.decorators.data = monkey_data

# Copy back the docstring to allow Sphinx generate the documentation for the
# robottelo wrapper
robottelo.decorators.data.__doc__ = robottelo_data_docstring
