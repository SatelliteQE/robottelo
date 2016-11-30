from robottelo.populate.base import BasePopulator


class CLIPopulator(BasePopulator):
    """Populates system using hammer"""

    def populate(self):
        """reads the list of entities and populates the
        system"""
