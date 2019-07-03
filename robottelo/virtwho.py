"""Utilities for Virtwho Configure Plugin Testing

All the virtwho-configure UI/CLI/API interfaces should be defined there.

"""
from robottelo.config import settings


def get_hypervisor_type():
    return{
        'esx': 'VMware vSphere / vCenter (esx)',
        'xen': 'XenServer (xen)',
        'rhevm': 'Red Hat Virtualization Hypervisor (rhevm)',
        'hyperv': 'Microsoft Hyper-V (hyperv)',
        'libvirt': 'libvirt',
        'kubevirt': 'Container-native virtualization',
    }


def get_form_data(
        name, debug=True, interval='Every hour', hypervisor_id='hostname'):
    hypervisor = settings.virtwho.hypervisor_type
    hypervisor_type = get_hypervisor_type()[hypervisor]
    hypervisor_server = settings.virtwho.hypervisor_server
    form_data = {
        'name': name,
        'debug': debug,
        'interval': interval,
        'hypervisor_id': hypervisor_id,
        'hypervisor_type': hypervisor_type,
        'hypervisor_content.server': hypervisor_server,
    }
    if hypervisor == 'libvirt':
        form_data['hypervisor_content.username'] = (
                settings.virtwho.hypervisor_username)
    elif hypervisor == 'kubevirt':
        form_data['hypervisor_content.kubeconfig'] = (
                settings.virtwho.hypervisor_config_file)
    else:
        form_data['hypervisor_content.username'] = (
                settings.virtwho.hypervisor_username)
        form_data['hypervisor_content.password'] = (
                settings.virtwho.hypervisor_password)
    return form_data
