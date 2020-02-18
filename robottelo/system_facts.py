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


ARCHITECTURES = [u"i386", u"x86_64", u"ppc", u's390x']

# https://en.wikipedia.org/wiki/Red_Hat_Enterprise_Linux#Version_history
DISTRO_IDS = [
    {
        u'id': u'Maipo',
        u'version': u'7.0',
        # There is no 'i386' for RHEL 7
        u'architecture': gen_choice(ARCHITECTURES[1:]),
        u'kernel': u'3.10.0-123.el7',
    },
    {
        u'id': u'Santiago',
        u'version': u'6.{0}'.format(gen_integer(1, 5)),
        u'architecture': gen_choice(ARCHITECTURES),
        u'kernel': u'2.6.32-431.el6',
    },
    {
        u'id': u'Tikanga',
        u'version': u'5.{0}'.format(gen_integer(1, 10)),
        u'architecture': gen_choice(ARCHITECTURES),
        u'kernel': u'2.6.18-371.el5',
    },
    {
        u'id': u'Nahant',
        u'version': u'4.{0}'.format(gen_integer(1, 9)),
        # Assuming only 'i386' and 'x86_64'
        u'architecture': gen_choice(ARCHITECTURES[:2]),
        u'kernel': u'2.6.9-100.el4',
    },
    {
        u'id': u'Taroon',
        u'version': u'3.{0}'.format(gen_integer(1, 9)),
        # Assuming only 'i386' and 'x86_64'
        u'architecture': gen_choice(ARCHITECTURES[:2]),
        u'kernel': u'2.4.21-50.el3',
    },
    {
        u'id': u'Pensacola',
        u'version': u'2.{0}'.format(gen_integer(1, 7)),
        # Assuming only 'i386' and 'x86_64'
        u'architecture': gen_choice(ARCHITECTURES[:2]),
        u'kernel': u'2.4.9-e.57.el2',
    },
]

MEMORY_CAPACITY = [u"2 GB", u"4 GB", u"8 GB", u"16 GB"]

MEMORY_SIZE = [u"1024 MB", u"2048 MB", u"4096 MB", u"8192 MB"]

SYSTEM_FACTS = {
    u'cpu.core(s)_per_socket': u'1',
    u'cpu.cpu(s)': u'1',
    u'cpu.cpu_socket(s)': u'1',
    u'distribution.id': None,
    u'distribution.name': u'Red Hat Enterprise Linux Server',
    u'distribution.version': None,
    u'dmi.bios.address': u'0xe8000',
    u'dmi.bios.bios_revision': u'1.0',
    u'dmi.bios.relase_date': None,
    u'dmi.bios.rom_size': u'64 KB',
    u'dmi.bios.runtime_size': u'96 KB',
    u'dmi.bios.vendor': u'Seabios',
    u'dmi.bios.version': u'0.5.1',
    u'dmi.chassis.asset_tag': u'Not Specified',
    u'dmi.chassis.boot-up_state': u'Safe',
    u'dmi.chassis.lock': u'Not Present',
    u'dmi.chassis.manufacturer': u'Red Hat',
    u'dmi.chassis.power_supply_state': u'Safe',
    u'dmi.chassis.security_status': u'Unknown',
    u'dmi.chassis.serial_number': u'Not Specified',
    u'dmi.chassis.thermal_state': u'Safe',
    u'dmi.chassis.type': u'Other',
    u'dmi.chassis.version': u'Not Specified',
    u'dmi.memory.array_handle': u'0x1000',
    u'dmi.memory.bank_locator': u'Not Specified',
    u'dmi.memory.data_width': u'64 bit',
    u'dmi.memory.error_correction_type': u'Multi-bit ECC',
    u'dmi.memory.error_information_handle': u'Not Provided',
    u'dmi.memory.form_factor': u'DIMM',
    u'dmi.memory.location': u'Other',
    u'dmi.memory.locator': u'DIMM 0',
    u'dmi.memory.maximum_capacity': None,
    u'dmi.memory.size': None,
    u'dmi.memory.speed': u'  (ns)',
    u'dmi.memory.total_width': u'64 bit',
    u'dmi.memory.type': u'RAM',
    u'dmi.memory.use': u'System Memory',
    u'dmi.processor.family': u'Other',
    u'dmi.processor.socket_designation': u'CPU 1',
    u'dmi.processor.status': u'Populated:Enabled',
    u'dmi.processor.type': u'Central Processor',
    u'dmi.processor.upgrade': u'Other',
    u'dmi.processor.version': u'Not Specified',
    u'dmi.processor.voltage': u' ',
    u'dmi.system.family': u'Red Hat Enterprise Linux',
    u'dmi.system.manufacturer': u'Red Hat',
    u'dmi.system.product_name': u'KVM',
    u'dmi.system.serial_number': u'Not Specified',
    u'dmi.system.sku_number': u'Not Specified',
    u'dmi.system.status': u'No errors detected',
    u'dmi.system.uuid': None,
    u'dmi.system.version': u'RHEL 6.2.0 PC',  #
    u'dmi.system.wake-up_type': u'Power Switch',
    u'lscpu.architecture': None,
    u'lscpu.bogomips': u'4200.01',
    u'lscpu.byte_order': u'Little Endian',
    u'lscpu.core(s)_per_socket': u'1',
    u'lscpu.cpu(s)': u'1',
    u'lscpu.cpu_family': u'6',
    u'lscpu.cpu_mhz': u'2100.008',
    u'lscpu.cpu_op-mode(s)': u'32-bit, 64-bit',
    u'lscpu.cpu_socket(s)': u'1',
    u'lscpu.hypervisor_vendor': u'KVM',
    u'lscpu.l1d_cache': u'64K',
    u'lscpu.l1i_cache': u'64K',
    u'lscpu.l2_cache': u'512K',
    u'lscpu.model': u'13',
    u'lscpu.numa_node(s)': u'1',
    u'lscpu.numa_node0_cpu(s)': u'0',
    u'lscpu.on-line_cpu(s)_list': u'0',
    u'lscpu.stepping': u'3',
    u'lscpu.thread(s)_per_core': u'1',
    u'lscpu.vendor_id': u'AuthenticAMD',
    u'lscpu.virtualization_type': u'full',
    u'memory.memtotal': u'2055092',
    u'memory.swaptotal': u'2064376',
    u'net.interface.eth1.broadcast': u'10.10.169.255',
    u'net.interface.eth1.hwaddr': None,
    u'net.interface.eth1.ipaddr': None,
    u'net.interface.eth1.netmask': u'255.255.254.0',
    u'net.interface.lo.broadcast': u'0.0.0.0',
    u'net.interface.lo.hwaddr': u'00:00:00:00:00:00',
    u'net.interface.lo.ipaddr': u'127.0.0.1',
    u'net.interface.lo.netmask': u'255.0.0.0',
    u'network.hostname': None,
    u'network.ipaddr': None,
    u'system.entitlements_valid': u'false',
    u'uname.machine': None,
    u'uname.nodename': None,
    u'uname.release': None,
    u'uname.sysname': u'Linux',
    u'uname.version': u'#1 SMP Wed Nov 9 08:03:13 EST 2011',
    u'virt.host_type': u'kvm',
    u'virt.is_guest': u'true',
    u'virt.uuid': None,
}


def generate_system_facts(name=None):
    """Generate random system facts for registration.

    :param str name: A valid FQDN for a system. If one is not
        provided, then a random value will be generated.
    :return: A dictionary with random system facts
    :rtype: dict
    """
    if name is None:
        name = u'{0}.example.net'.format(gen_alpha().lower())

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
    new_facts['dmi.system.version'] = u'RHEL'
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
