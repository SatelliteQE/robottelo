# -*- encoding: utf-8 -*-
"""Implements Docker Tags UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class DockerTag(Base):
    """Manipulates Docker Tags from UI"""

    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Docker Tag entity page"""
        Navigator(self.browser).go_to_docker_tags()

    def _search_locator(self):
        """Specify locator for Docker Tag entity search procedure"""
        return locators['dockertag.select_name']

    def search(self, name, product_name, repo_name):
        """Use custom search as entity locator value depends on docker tag
        name, product name and repository name.
        """
        return super(DockerTag, self).search((name, product_name, repo_name))
