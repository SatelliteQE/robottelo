"""
This module contains helper code used by the ``tests.foreman`` module.

This module is subservient to the ``tests.foreman`` module, and exists soley
for the sake of helping that module get its work done. For example, the
``tests.foreman.api`` module relies upon the ``robottelo.api`` module, and the
``tests.foreman.cli`` module relies upon the ``robottelo.cli`` module. More
generally: code in the ``tests`` module calls code in the ``robottelo`` module,
but not the other way around.
"""
