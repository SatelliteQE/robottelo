#!/usr/bin/env python2
#
# Do *NOT* rename this file to `pylint.py`. Though such is a better name, it
# runs afoul of Python 2 import issues.
"""Logic for linting Python files in this application with Pylint."""
from pylint.lint import Run
import os


def lint():
    """Search for Python source files and lint them with Pylint."""
    # Let's do some prep work before finding files to lint.
    this_file = os.path.realpath(__file__)
    this_dir = os.path.dirname(this_file)
    search_paths = (
        os.path.join(this_dir, 'robottelo'),
        os.path.join(this_dir, 'tests'),
    )

    # Prep work done. Time to find files! Yeah, this is a stupid amount of
    # nested logic.
    targets = [this_file]
    for search_path in search_paths:
        for root, dirs, files in os.walk(search_path):  # pylint: disable=W0612
            for file_ in files:
                if file_.endswith('.py'):
                    targets.append(os.path.join(root, file_))

    # All files should be linted at the same time. Doing so allows for summary
    # statistics about all files in this project, and also allows repeated
    # setup/teardown work to be avoided.
    Run(targets)

if __name__ == '__main__':
    lint()
