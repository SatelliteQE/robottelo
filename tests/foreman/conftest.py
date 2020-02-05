# coding: utf-8
"""Configurations for py.test runner"""
import datetime

import logging

import pytest
try:
    from pytest_reportportal import RPLogger, RPLogHandler
except ImportError:
    pass
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import (
    AZURERM_RHEL7_FT_IMG_URN,
    AZURERM_RHEL7_UD_IMG_URN,
    AZURERM_RG_DEFAULT,
    DEFAULT_ARCHITECTURE,
    DEFAULT_TEMPLATE,
    DEFAULT_PXE_TEMPLATE,
    DEFAULT_PTABLE,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION
)
from robottelo.decorators import setting_is_set
from robottelo.helpers import download_gce_cert, generate_issue_collection, is_open
from wrapanapi import AzureSystem, GoogleCloudSystem


def log(message, level="DEBUG"):
    """Pytest has a limitation to use logging.logger from conftest.py
    so we need to emulate the logger by stdouting the output
    """
    now = datetime.datetime.utcnow()
    full_message = "{date} - conftest - {level} - {message}".format(
        date=now.strftime("%Y-%m-%d %H:%M:%S"),
        level=level,
        message=message
    )
    print(full_message)  # noqa
    with open('robottelo.log', 'a') as log_file:
        log_file.write(full_message)


def pytest_report_header(config):
    """Called when pytest session starts"""
    messages = []

    shared_function_enabled = 'OFF'
    scope = ''
    storage = 'file'
    if setting_is_set('shared_function'):
        if settings.shared_function.enabled:
            shared_function_enabled = 'ON'
        scope = settings.shared_function.scope
        if not scope:
            scope = ''
        storage = settings.shared_function.storage
    if pytest.config.pluginmanager.hasplugin("junitxml"):
        junit = getattr(config, "_xml", None)
        if junit is not None:
            now = datetime.datetime.utcnow()
            junit.add_global_property("start_time", now.strftime("%Y-%m-%dT%H:%M:%S"))
    messages.append(
        'shared_function enabled - {0} - scope: {1} - storage: {2}'.format(
            shared_function_enabled, scope, storage))

    return messages


@pytest.fixture(scope="session")
def worker_id(request):
    """Gets the worker ID when running in multi-threading with xdist
    """
    if hasattr(request.config, 'slaveinput'):
        # return gw+(0..n)
        return request.config.slaveinput['slaveid']
    else:
        return 'master'


@pytest.fixture(scope="session")
def configured_settings():
    if not settings.configured:
        settings.configure()
    return settings


@pytest.fixture(autouse=True, scope='module')
def robottelo_logger(request, worker_id):
    """Set up a separate logger for each pytest-xdist worker
    if worker_id != 'master' then xdist is running in multi-threading so
    a logfile named 'robottelo_gw{worker_id}.log' will be created.
    """
    logger = logging.getLogger('robottelo')
    if (hasattr(request.session.config, '_reportportal_configured') and
       request.session.config._reportportal_configured):
        logging.setLoggerClass(RPLogger)
    if '{0}'.format(worker_id) not in [h.get_name() for h in logger.handlers]:
        if worker_id != 'master':
            formatter = logging.Formatter(
                fmt='%(asctime)s - {0} - %(name)s - %(levelname)s -'
                    ' %(message)s'.format(worker_id),
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler = logging.FileHandler(
                'robottelo_{0}.log'.format(worker_id)
            )
            handler.set_name('{0}'.format(worker_id))
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            # Nailgun HTTP logs should also be included in gw* logs
            logging.getLogger('nailgun').addHandler(handler)
            if (hasattr(request.session.config, '_reportportal_configured') and
               request.session.config._reportportal_configured):
                rp_handler = RPLogHandler(request.node.config.py_test_service)
                rp_handler.set_name('{0}'.format(worker_id))
                rp_handler.setFormatter(formatter)
                logger.addHandler(rp_handler)
                logging.getLogger('nailgun').addHandler(rp_handler)
    return logger


@pytest.fixture(autouse=True)
def log_test_execution(robottelo_logger, request):
    test_name = request.node.name
    parent_name = request.node.parent.name
    test_full_name = '{}/{}'.format(parent_name, test_name)
    robottelo_logger.debug('Started Test: {}'.format(test_full_name))
    yield None
    robottelo_logger.debug('Finished Test: {}'.format(test_full_name))


def pytest_collection_modifyitems(items, config):
    """Called after collection has been performed, may filter or re-order
    the items in-place.
    """

    log("Collected %s test cases" % len(items))

    # First collect all issues in use and build an issue collection
    # This collection includes pre-processed `is_open` status for each issue
    # generate_issue_collection will save a file `bz_cache.json` on each run.
    pytest.issue_data = generate_issue_collection(items, config)

    # Modify items based on collected issue_data
    deselected_items = []

    for item in items:
        # 1. Deselect tests marked with @pytest.mark.deselect
        # WONTFIX BZs makes test to be dynamically marked as deselect.
        deselect = item.get_closest_marker('deselect')
        if deselect:
            deselected_items.append(item)
            reason = deselect.kwargs.get('reason', deselect.args)
            log(f"Deselected test '{item.name}' reason: {reason}")
            # Do nothing more with deselected tests
            continue

        # 2. Skip items based on skip_if_open marker
        skip_if_open = item.get_closest_marker('skip_if_open')
        if skip_if_open:
            # marker must have `BZ:123456` as argument.
            issue = skip_if_open.kwargs.get('reason') or skip_if_open.args[0]
            item.add_marker(pytest.mark.skipif(is_open(issue), reason=issue))

    config.hook.pytest_deselected(items=deselected_items)
    items[:] = [item for item in items if item not in deselected_items]


@pytest.fixture(autouse=True, scope="function")
def record_test_timestamp_xml(record_property):
    now = datetime.datetime.utcnow()
    record_property("start_time", now.strftime("%Y-%m-%dT%H:%M:%S"))


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "stubbed: Tests that are not automated yet.",
        "deselect(reason=None): Mark test to be removed from collection.",
        "skip_if_open(issue): Skip test based on issue status.",
        "tier1: Tier 1 tests",
        "tier2: Tier 2 tests",
        "tier3: Tier 3 tests",
        "tier4: Tier 4 tests",
        "destructive: Destructive tests",
        "upgrade: Upgrade tests",
        "run_in_one_thread: Sequential tests",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)

    # ignore warnings about dynamically added markers e.g: component markers
    config.addinivalue_line(
        'filterwarnings', 'ignore::pytest.PytestUnknownMarkWarning'
    )


def pytest_addoption(parser):
    """Adds custom options to pytest runner."""
    parser.addoption(
        "--bz-cache",
        nargs='?',
        default=None,
        const='bz_cache.json',
        help="Use a bz_cache.json instead of calling BZ API.",
    )


# Satellite Entities to be used by CLI, API andUI Tests #

# Global Satellite Entities

@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_location(module_org):
    return entities.Location(organization=[module_org]).create()


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='module')
def module_smart_proxy(module_location):
    smart_proxy = entities.SmartProxy().search(
        query={'search': 'name={0}'.format(
            settings.server.hostname)})[0].read()
    smart_proxy.location.append(entities.Location(id=module_location.id))
    smart_proxy.update(['location'])
    return entities.SmartProxy(id=smart_proxy.id).read()


@pytest.fixture(scope='module')
def module_domain(module_org, module_location, module_smart_proxy):
    return entities.Domain(
        dns=module_smart_proxy,
        location=[module_location],
        organization=[module_org]
    ).create()


@pytest.fixture(scope='module')
def module_subnet(module_org, module_location, module_domain, module_smart_proxy):
    network = settings.vlan_networking.subnet
    subnet = entities.Subnet(
            network=network,
            mask=settings.vlan_networking.netmask,
            domain=[module_domain],
            location=[module_location],
            organization=[module_org],
            dns=module_smart_proxy,
            dhcp=module_smart_proxy,
            tftp=module_smart_proxy,
            discovery=module_smart_proxy,
            ipam='DHCP'
        ).create()
    return subnet


@pytest.fixture(scope='module')
def module_partiontable(module_org, module_location):
    ptable = entities.PartitionTable().search(query={
        u'search': u'name="{0}"'.format(DEFAULT_PTABLE)})[0].read()
    ptable.location.append(module_location)
    ptable.organization.append(module_org)
    ptable.update(['location', 'organization'])
    return entities.PartitionTable(id=ptable.id).read()


@pytest.fixture(scope='module')
def module_provisioingtemplate(module_org, module_location):
    provisioning_template = entities.ProvisioningTemplate().search(
        query={
            u'search': u'name="{0}"'.format(DEFAULT_TEMPLATE)
        }
    )
    provisioning_template = provisioning_template[0].read()
    provisioning_template.organization.append(module_org)
    provisioning_template.location.append(module_location)
    provisioning_template.update(['organization', 'location'])
    provisioning_template = entities.ProvisioningTemplate(
        id=provisioning_template.id).read()
    return provisioning_template


@pytest.fixture(scope='module')
def module_configtemaplate(module_org, module_location):
    pxe_template = entities.ConfigTemplate().search(
        query={
            u'search': u'name="{0}"'.format(DEFAULT_PXE_TEMPLATE)
        }
    )
    pxe_template = pxe_template[0].read()
    pxe_template.organization.append(module_org)
    pxe_template.location.append(module_location)
    pxe_template.update(['organization', 'location'])
    pxe_template = entities.ConfigTemplate(id=pxe_template.id).read()
    return pxe_template


@pytest.fixture(scope='module')
def module_architecture():
    arch = entities.Architecture().search(
        query={
            u'search': u'name="{0}"'.format(DEFAULT_ARCHITECTURE)
        }
    )[0].read()
    return arch


@pytest.fixture(scope='module')
def module_os(
        module_architecture, module_partiontable, module_configtemaplate,
        module_provisioingtemplate, os=None):
    if os is None:
        os = entities.OperatingSystem().search(query={
            u'search': u'name="RedHat" AND (major="{0}" OR major="{1}")'.format(
                RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
        })[0].read()
    else:
        os = entities.OperatingSystem().search(query={
            u'search': u'family="Redhat" AND major="{0}" AND minor="{1}")'.format(
                os.split(' ')[1].split('.')[0], os.split(' ')[1].split('.')[1])
        })[0].read()
    os.architecture.append(module_architecture)
    os.ptable.append(module_partiontable)
    os.config_template.append(module_configtemaplate)
    os.provisioning_template.append(module_provisioingtemplate)
    os.update([
        'architecture',
        'ptable',
        'config_template',
        'provisioning_template'
    ])
    os = entities.OperatingSystem(id=os.id).read()
    return os


@pytest.fixture(scope='module')
def module_puppet_environment(module_org, module_location):
    environments = entities.Environment().search(
        query=dict(search='organization_id={0}'.format(module_org.id)))
    if len(environments) > 0:
        environment = environments[0].read()
        environment.location.append(module_location)
        environment = environment.update(['location'])
    else:
        environment = entities.Environment(
            organization=[module_org],
            location=[module_location]
        ).create()
    puppetenv = entities.Environment(id=environment.id).read()
    return puppetenv


# Google Cloud Engine Entities
@pytest.fixture(scope='session')
def googleclient():
    gceclient = GoogleCloudSystem(
        project=settings.gce.project_id,
        zone=settings.gce.zone,
        file_path=download_gce_cert(),
        file_type='json')
    yield gceclient
    gceclient.disconnect()


@pytest.fixture(scope='session')
def gce_latest_rhel_uuid(googleclient):
    template_names = [img.name for img in googleclient.list_templates(True)]
    latest_rhel7_template = max(name for name in template_names if name.startswith('rhel-7'))
    latest_rhel7_uuid = googleclient.get_template(latest_rhel7_template, project='rhel-cloud').uuid
    return latest_rhel7_uuid


@pytest.fixture(scope='session')
def gce_custom_cloudinit_uuid(googleclient):
    cloudinit_uuid = googleclient.get_template(
        'customcinit', project=settings.gce.project_id).uuid
    return cloudinit_uuid


@pytest.fixture(scope='module')
def module_gce_compute(module_org, module_location):
    gce_cr = entities.GCEComputeResource(
        name=gen_string('alphanumeric'), provider='GCE', email=settings.gce.client_email,
        key_path=settings.gce.cert_path, project=settings.gce.project_id,
        zone=settings.gce.zone, organization=[module_org],
        location=[module_location]).create()
    return gce_cr


@pytest.fixture(scope='module')
def azurerm_settings():
    deps = {
        'tenant': settings.azurerm.tenant_id,
        'app_ident': settings.azurerm.client_id,
        'sub_id': settings.azurerm.subscription_id,
        'secret': settings.azurerm.client_secret,
        'region': settings.azurerm.azure_region.lower().replace(' ', ''),
    }
    return deps


@pytest.fixture(scope='module')
def module_azurerm_cr(azurerm_settings, module_org, module_location):
    """ Create AzureRM Compute Resource """
    azure_cr = entities.AzureRMComputeResource(
        name=gen_string('alpha'),
        provider='AzureRm',
        tenant=azurerm_settings['tenant'],
        app_ident=azurerm_settings['app_ident'],
        sub_id=azurerm_settings['sub_id'],
        secret_key=azurerm_settings['secret'],
        region=azurerm_settings['region'],
        organization=[module_org],
        location=[module_location],
    ).create()
    return azure_cr


@pytest.fixture(scope='module')
def module_azurerm_finishimg(module_architecture, module_os, module_azurerm_cr):
    """ Creates Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=module_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=module_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_IMG_URN
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_cloudimg(module_architecture, module_os, module_azurerm_cr):
    """ Creates cloudinit image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=module_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=module_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_UD_IMG_URN,
        user_data=True
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def azurermclient(azurerm_settings):
    """ Connect to AzureRM using wrapanapi AzureSystem"""
    azurermclient = AzureSystem(
        username=azurerm_settings['app_ident'],
        password=azurerm_settings['secret'],
        tenant_id=azurerm_settings['tenant'],
        subscription_id=azurerm_settings['sub_id'],
        provisioning={
            "resource_group": AZURERM_RG_DEFAULT,
            "template_container": None,
            "region_api": azurerm_settings['region']})
    yield azurermclient
    azurermclient.disconnect()
