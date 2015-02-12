"""Tests for the ``hostgroups`` paths."""
from robottelo.common.decorators import stubbed
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


class HostGroupTestCaseStub(APITestCase):
    """Incomplete tests for host groups.

    When implemented, each of these tests should probably be data-driven. A
    decorator of this form might be used::

        @data(
            name is alpha,
            name is alpha_numeric,
            name is html,
            name is latin1,
            name is numeric,
            name is utf-8,
        )

    """

    @stubbed()
    def test_remove_hostgroup_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_remove_hostgroup_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        ID and hostgroup name
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_remove_hostgroup_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup ID
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_remove_hostgroup_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        ID and hostgroup ID
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        ID and hostgroup name
        @assert: hostgroup is added to organization
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        name and hostgroup ID
        @assert: hostgroup is added to organization
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        ID and hostgroup ID
        @assert: hostgroup is added to organization
        @status: manual
        """
