import pytest

from robottelo.cli.ansible import Ansible


@pytest.fixture(scope="session")
def import_ansible_roles(default_smart_proxy):
    """Import ansible roles to default_smart_proxy for tests"""
    Ansible.roles_import({'proxy-id': default_smart_proxy.id})
    Ansible.variables_import({'proxy-id': default_smart_proxy.id})
