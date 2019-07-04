"""Utilities for Virtwho Configure Plugin Testing

All the virtwho-configure UI/CLI/API interfaces should be defined there.

"""
from robottelo.config import settings


def get_form_data(name):
    hypervisor_type = settings.virtwho.hypervisor_type
    hypervisor_server = settings.virtwho.hypervisor_server
    form_data = {
        'name': name,
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': hypervisor_type,
        'hypervisor_content.server': hypervisor_server,
    }
    if hypervisor_type == 'libvirt':
        form_data['hypervisor_content.username'] = (
            settings.virtwho.hypervisor_username)
    elif hypervisor_type == 'kubevirt':
        form_data['hypervisor_content.kubeconfig'] = (
            settings.virtwho.hypervisor_config_file)
    else:
        form_data['hypervisor_content.username'] = (
            settings.virtwho.hypervisor_username)
        form_data['hypervisor_content.password'] = (
            settings.virtwho.hypervisor_password)
    return form_data
