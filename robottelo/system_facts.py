"""JSON representation for a RHEL server."""
import copy
import datetime

from fauxfactory import gen_alpha
from fauxfactory import gen_choice
from fauxfactory import gen_date
from fauxfactory import gen_integer
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_uuid


def _bios_date():
    """Generate a random date for system's BIOS between
    today and 10 years ago.

    :return: A random `datetime.date` that falls within the last 10 years
        from today.
    :rtype: object

    """
    # Today is...
    today = datetime.date.today()
    # and 10 years ago (~365 days * 10 years) is
    ten_years_ago = today - datetime.timedelta(3650)
    return gen_date(ten_years_ago, today)


ARCHITECTURES = ["i386", "x86_64", "ppc", 's390x']

# https://en.wikipedia.org/wiki/Red_Hat_Enterprise_Linux#Version_history
DISTRO_IDS = [
    {
        'id': 'Maipo',
        'version': '7.0',
        # There is no 'i386' for RHEL 7
        'architecture': gen_choice(ARCHITECTURES[1:]),
        'kernel': '3.10.0-123.el7',
    },
    {
        'id': 'Santiago',
        'version': f'6.{gen_integer(1, 5)}',
        'architecture': gen_choice(ARCHITECTURES),
        'kernel': '2.6.32-431.el6',
    },
    {
        'id': 'Tikanga',
        'version': f'5.{gen_integer(1, 10)}',
        'architecture': gen_choice(ARCHITECTURES),
        'kernel': '2.6.18-371.el5',
    },
    {
        'id': 'Nahant',
        'version': f'4.{gen_integer(1, 9)}',
        # Assuming only 'i386' and 'x86_64'
        'architecture': gen_choice(ARCHITECTURES[:2]),
        'kernel': '2.6.9-100.el4',
    },
    {
        'id': 'Taroon',
        'version': f'3.{gen_integer(1, 9)}',
        # Assuming only 'i386' and 'x86_64'
        'architecture': gen_choice(ARCHITECTURES[:2]),
        'kernel': '2.4.21-50.el3',
    },
    {
        'id': 'Pensacola',
        'version': f'2.{gen_integer(1, 7)}',
        # Assuming only 'i386' and 'x86_64'
        'architecture': gen_choice(ARCHITECTURES[:2]),
        'kernel': '2.4.9-e.57.el2',
    },
]

MEMORY_CAPACITY = ["2 GB", "4 GB", "8 GB", "16 GB"]

MEMORY_SIZE = ["1024 MB", "2048 MB", "4096 MB", "8192 MB"]

SYSTEM_FACTS = {
    'cpu.core(s)_per_socket': '1',
    'cpu.cpu(s)': '1',
    'cpu.cpu_socket(s)': '1',
    'distribution.id': None,
    'distribution.name': 'Red Hat Enterprise Linux Server',
    'distribution.version': None,
    'dmi.bios.address': '0xe8000',
    'dmi.bios.bios_revision': '1.0',
    'dmi.bios.relase_date': None,
    'dmi.bios.rom_size': '64 KB',
    'dmi.bios.runtime_size': '96 KB',
    'dmi.bios.vendor': 'Seabios',
    'dmi.bios.version': '0.5.1',
    'dmi.chassis.asset_tag': 'Not Specified',
    'dmi.chassis.boot-up_state': 'Safe',
    'dmi.chassis.lock': 'Not Present',
    'dmi.chassis.manufacturer': 'Red Hat',
    'dmi.chassis.power_supply_state': 'Safe',
    'dmi.chassis.security_status': 'Unknown',
    'dmi.chassis.serial_number': 'Not Specified',
    'dmi.chassis.thermal_state': 'Safe',
    'dmi.chassis.type': 'Other',
    'dmi.chassis.version': 'Not Specified',
    'dmi.memory.array_handle': '0x1000',
    'dmi.memory.bank_locator': 'Not Specified',
    'dmi.memory.data_width': '64 bit',
    'dmi.memory.error_correction_type': 'Multi-bit ECC',
    'dmi.memory.error_information_handle': 'Not Provided',
    'dmi.memory.form_factor': 'DIMM',
    'dmi.memory.location': 'Other',
    'dmi.memory.locator': 'DIMM 0',
    'dmi.memory.maximum_capacity': None,
    'dmi.memory.size': None,
    'dmi.memory.speed': '  (ns)',
    'dmi.memory.total_width': '64 bit',
    'dmi.memory.type': 'RAM',
    'dmi.memory.use': 'System Memory',
    'dmi.processor.family': 'Other',
    'dmi.processor.socket_designation': 'CPU 1',
    'dmi.processor.status': 'Populated:Enabled',
    'dmi.processor.type': 'Central Processor',
    'dmi.processor.upgrade': 'Other',
    'dmi.processor.version': 'Not Specified',
    'dmi.processor.voltage': ' ',
    'dmi.system.family': 'Red Hat Enterprise Linux',
    'dmi.system.manufacturer': 'Red Hat',
    'dmi.system.product_name': 'KVM',
    'dmi.system.serial_number': 'Not Specified',
    'dmi.system.sku_number': 'Not Specified',
    'dmi.system.status': 'No errors detected',
    'dmi.system.uuid': None,
    'dmi.system.version': 'RHEL 6.2.0 PC',  #
    'dmi.system.wake-up_type': 'Power Switch',
    'lscpu.architecture': None,
    'lscpu.bogomips': '4200.01',
    'lscpu.byte_order': 'Little Endian',
    'lscpu.core(s)_per_socket': '1',
    'lscpu.cpu(s)': '1',
    'lscpu.cpu_family': '6',
    'lscpu.cpu_mhz': '2100.008',
    'lscpu.cpu_op-mode(s)': '32-bit, 64-bit',
    'lscpu.cpu_socket(s)': '1',
    'lscpu.hypervisor_vendor': 'KVM',
    'lscpu.l1d_cache': '64K',
    'lscpu.l1i_cache': '64K',
    'lscpu.l2_cache': '512K',
    'lscpu.model': '13',
    'lscpu.numa_node(s)': '1',
    'lscpu.numa_node0_cpu(s)': '0',
    'lscpu.on-line_cpu(s)_list': '0',
    'lscpu.stepping': '3',
    'lscpu.thread(s)_per_core': '1',
    'lscpu.vendor_id': 'AuthenticAMD',
    'lscpu.virtualization_type': 'full',
    'memory.memtotal': '2055092',
    'memory.swaptotal': '2064376',
    'net.interface.eth1.broadcast': '10.10.169.255',
    'net.interface.eth1.hwaddr': None,
    'net.interface.eth1.ipaddr': None,
    'net.interface.eth1.netmask': '255.255.254.0',
    'net.interface.lo.broadcast': '0.0.0.0',
    'net.interface.lo.hwaddr': '00:00:00:00:00:00',
    'net.interface.lo.ipaddr': '127.0.0.1',
    'net.interface.lo.netmask': '255.0.0.0',
    'network.hostname': None,
    'network.ipaddr': None,
    'system.entitlements_valid': 'false',
    'uname.machine': None,
    'uname.nodename': None,
    'uname.release': None,
    'uname.sysname': 'Linux',
    'uname.version': '#1 SMP Wed Nov 9 08:03:13 EST 2011',
    'virt.host_type': 'kvm',
    'virt.is_guest': 'true',
    'virt.uuid': None,
}


def generate_system_facts(name=None):
    """Generate random system facts for registration.

    :param str name: A valid FQDN for a system. If one is not
        provided, then a random value will be generated.
    :return: A dictionary with random system facts
    :rtype: dict
    """
    if name is None:
        name = f'{gen_alpha().lower()}.example.net'

    # Make a copy of the system facts 'template'
    new_facts = copy.deepcopy(SYSTEM_FACTS)
    # Select a random RHEL version...
    distro = gen_choice(DISTRO_IDS)

    # ...and update our facts
    new_facts['distribution.id'] = distro['id']
    new_facts['distribution.version'] = distro['version']
    new_facts['dmi.bios.relase_date'] = _bios_date().strftime('%m/%d/%Y')
    new_facts['dmi.memory.maximum_capacity'] = gen_choice(MEMORY_CAPACITY)
    new_facts['dmi.memory.size'] = gen_choice(MEMORY_SIZE)
    new_facts['dmi.system.uuid'] = gen_uuid()
    new_facts['dmi.system.version'] = 'RHEL'
    new_facts['lscpu.architecture'] = distro['architecture']
    new_facts['net.interface.eth1.hwaddr'] = gen_mac(multicast=False)
    new_facts['net.interface.eth1.ipaddr'] = gen_ipaddr()
    new_facts['network.hostname'] = name
    new_facts['network.ipaddr'] = new_facts['net.interface.eth1.ipaddr']
    new_facts['uname.machine'] = distro['architecture']
    new_facts['uname.nodename'] = name
    new_facts['uname.release'] = distro['kernel']
    new_facts['virt.uuid'] = new_facts['dmi.system.uuid']

    return new_facts
