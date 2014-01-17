# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Organization CLI
"""

from robottelo.cli.factory import (
    make_domain, make_environment, make_hostgroup, make_medium, make_org,
    make_proxy, make_subnet, make_template, make_user)
from robottelo.cli.org import Org
from tests.cli.basecli import MetaCLI


class TestOrg(MetaCLI):

    factory = make_org
    factory_obj = Org

    def test_create_org(self):
        """Org Creation - Successfully creates a new org"""
        result = make_org()
        org_info = Org().info({'name': result['name']})
        #TODO: Assert fails currently for an existing bug
        self.assertEqual(result['name'], org_info.stdout['name'])

    def test_delete_org(self):
        """Org Deletion - Successfully deletes an org"""
        result = make_org()
        return_value = Org().delete({'name': result['name']})
        self.assertEqual(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_list_org(self):
        """Org list - Successfully displays the list of available orgs"""
        return_value = Org().list()
        self.assertEqual(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_info_org(self):
        """Org info - Successfully displays the info of an org"""
        result = make_org()
        return_value = Org().info({'name': result['name']})
        self.assertEqual(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_subnet(self):
        """Add a subnet to an org"""
        org_result = make_org()
        subnet_result = make_subnet()
        return_value = Org().add_subnet(
            {'name': org_result['name'], 'subnet': subnet_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_subnet(self):
        """Remove a subnet from an org"""
        org_result = make_org()
        subnet_result = make_subnet()
        Org().add_subnet(
            {'name': org_result['name'], 'subnet': subnet_result['name']})
        return_value = Org().remove_subnet(
            {'name': org_result['name'], 'subnet': subnet_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_domain(self):
        """Add a domain to an org"""
        org_result = make_org()
        domain_result = make_domain()
        return_value = Org().add_domain(
            {'name': org_result['name'], 'domain': domain_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_domain(self):
        """Removes a domain from an org"""
        org_result = make_org()
        domain_result = make_domain()
        Org().add_domain(
            {'name': org_result['name'], 'domain': domain_result['name']})
        return_value = Org().remove_domain(
            {'name': org_result['name'], 'domain': domain_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_user(self):
        """Adds a user in an org"""
        org_result = make_org()
        user_result = make_user()
        return_value = Org().add_user(
            {'name': org_result['name'], 'user-id': user_result['login']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_user(self):
        """Removes a user from an org"""
        org_result = make_org()
        user_result = make_user()
        Org().add_user(
            {'name': org_result['name'], 'user-id': user_result['login']})
        return_value = Org().remove_user(
            {'name': org_result['name'], 'user-id': user_result['login']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_hostgroup(self):
        """Adds a hostgroup in an org"""
        org_result = make_org()
        hostgroup_result = make_hostgroup()
        return_value = Org().add_hostgroup({
            'name': org_result['name'],
            'hostgroup': hostgroup_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_hostgroup(self):
        """Removes a hostgroup from an org"""
        org_result = make_org()
        hostgroup_result = make_hostgroup()
        Org().add_hostgroup({
            'name': org_result['name'],
            'hostgroup': hostgroup_result['name']})
        return_value = Org().remove_hostgroup({
            'name': org_result['name'],
            'hostgroup': hostgroup_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_computeresource(self):
        """Adds a computeresource in an org"""
        #TODO: Test should be done once computeresource base class is added
        pass

    def test_remove_computeresource(self):
        """Removes a compute resource in an org"""
        #TODO: Test should be done once computeresource base class is added
        pass

    def test_add_medium(self):
        """Adds a medium in an org"""
        org_result = make_org()
        medium_result = make_medium()
        return_value = Org().add_medium({
            'name': org_result['name'],
            'medium': medium_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_medium(self):
        """Removes a medium from an org"""
        org_result = make_org()
        medium_result = make_medium()
        Org().add_medium({
            'name': org_result['name'],
            'medium': medium_result['name']})
        return_value = Org().remove_medium({
            'name': org_result['name'],
            'medium': medium_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_configtemplate(self):
        """Adds a configtemplate to an org"""
        org_result = make_org()
        template_result = make_template()
        return_value = Org().add_configtemplate({
            'name': org_result['name'],
            'configtemplate': template_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_configtemplate(self):
        """Removes a configtemplate from an org"""
        org_result = make_org()
        template_result = make_template()
        Org().add_configtemplate({
            'name': org_result['name'],
            'configtemplate': template_result['name']})
        return_value = Org().remove_configtemplate({
            'name': org_result['name'],
            'configtemplate': template_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_environment(self):
        """Adds an environment to an org"""
        org_result = make_org()
        env_result = make_environment()
        return_value = Org().add_environment({
            'name': org_result['name'],
            'environment': env_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_environment(self):
        """Removes an environment from an org"""
        org_result = make_org()
        env_result = make_environment()
        Org().add_environment({
            'name': org_result['name'],
            'environment': env_result['name']})
        return_value = Org().remove_environment({
            'name': org_result['name'],
            'environment': env_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_add_smartproxy(self):
        """Adds a smartproxy to an org"""
        org_result = make_org()
        proxy_result = make_proxy()
        return_value = Org().add_proxy({
            'name': org_result['name'],
            'proxy': proxy_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)

    def test_remove_smartproxy(self):
        """Removes a smartproxy from an org"""
        org_result = make_org()
        proxy_result = make_proxy()
        Org().add_proxy({
            'name': org_result['name'],
            'proxy': proxy_result['name']})
        return_value = Org().remove_proxy({
            'name': org_result['name'],
            'proxy': proxy_result['name']})
        self.assertTrue(return_value.return_code, 0)
        self.assertFalse(return_value.stderr)
