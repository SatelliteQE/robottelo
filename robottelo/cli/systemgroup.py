# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""

"""

from robottelo.cli.base import Base


class Systemgroup(Base):
    """
    Manipulates Katello engine's systemgroup command.
    """

    command_base = "systemgroup"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
