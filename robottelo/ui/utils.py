from fauxfactory import gen_string

from robottelo.constants import DEFAULT_CV
from robottelo.constants import ENVIRONMENT


def create_fake_host(
    session,
    host,
    interface_id=gen_string('alpha'),
    global_parameters=None,
    host_parameters=None,
    extra_values=None,
):
    if extra_values is None:
        extra_values = {}
    os_name = f'{host.operatingsystem.name} {host.operatingsystem.major}'
    name = host.name if host.name is not None else gen_string('alpha').lower()
    values = {
        'host.name': name,
        'host.organization': host.organization.name,
        'host.location': host.location.name,
        'host.lce': ENVIRONMENT,
        'host.content_view': DEFAULT_CV,
        'operating_system.architecture': host.architecture.name,
        'operating_system.operating_system': os_name,
        'operating_system.media_type': 'All Media',
        'operating_system.media': host.medium.name,
        'operating_system.ptable': host.ptable.name,
        'operating_system.root_password': host.root_pass,
        'interfaces.interface.interface_type': 'Interface',
        'interfaces.interface.device_identifier': interface_id,
        'interfaces.interface.mac': host.mac,
        'interfaces.interface.domain': host.domain.name,
        'interfaces.interface.primary': True,
        'interfaces.interface.interface_additional_data.virtual_nic': False,
        'parameters.global_params': global_parameters,
        'parameters.host_params': host_parameters,
        'additional_information.comment': 'Host with fake data',
    }
    values.update(extra_values)
    session.host.create(values)
    return f'{name}.{host.domain.name}'
