"""This module contains helper code used by :mod:`tests.foreman` module.

This module is subservient to :mod:`tests.foreman`, and exists soley for the
sake of helping that module get its work done. For example,
:mod:`tests.foreman.cli` relies upon :mod:`robottelo.cli`.  More generally:
code in :mod:`tests` calls code in :mod:`robottelo`, but not the other way
around.

"""
from robottelo.helpers import configure_entities

configure_entities()
