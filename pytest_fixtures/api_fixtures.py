# Module-wide Nailgun Entity Fixtures to be used by API, CLI and UI Tests
import pytest
from fauxfactory import gen_string
from nailgun import entities
from wrapanapi import AzureSystem
from wrapanapi import GoogleCloudSystem

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import AZURERM_RG_DEFAULT
from robottelo.constants import AZURERM_RHEL7_FT_BYOS_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_CUSTOM_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_GALLERY_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_IMG_URN
from robottelo.constants import AZURERM_RHEL7_UD_IMG_URN
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_PXE_TEMPLATE
from robottelo.constants import DEFAULT_TEMPLATE
from robottelo.constants import ENVIRONMENT
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.helpers import download_gce_cert
from robottelo.test import settings

# Global Satellite Entities

if not settings.configured:
    settings.configure()


@pytest.fixture(scope='session')
def default_org():
    return entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]


@pytest.fixture(scope='session')
def default_location():
    return entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0]


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_location(module_org):
    return entities.Location(organization=[module_org]).create()


@pytest.fixture(scope='session')
def default_lce():
    return entities.LifecycleEnvironment().search(query={'search': f'name={ENVIRONMENT}'})[0]


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='module')
def module_host():
    return entities.Host().create()


@pytest.fixture(scope='module')
def module_model():
    return entities.Model().create()


@pytest.fixture(scope='module')
def module_compute_profile():
    return entities.ComputeProfile().create()


@pytest.fixture(scope='session')
def default_domain(default_smart_proxy):
    domain_name = settings.server.hostname.partition('.')[-1]
    dom = entities.Domain().search(query={'search': f'name={domain_name}'})[0]
    dom.dns = default_smart_proxy
    dom.update(['dns'])
    return entities.Domain(id=dom.id).read()


@pytest.fixture(scope='module')
def module_domain(module_org, module_location):
    return entities.Domain(location=[module_location], organization=[module_org]).create()


@pytest.fixture(scope='module')
def module_subnet(module_org, module_location, default_domain, default_smart_proxy):
    network = settings.vlan_networking.subnet
    subnet = entities.Subnet(
        network=network,
        mask=settings.vlan_networking.netmask,
        domain=[default_domain],
        location=[module_location],
        organization=[module_org],
        dns=default_smart_proxy,
        dhcp=default_smart_proxy,
        tftp=default_smart_proxy,
        discovery=default_smart_proxy,
        ipam='DHCP',
    ).create()
    return subnet


@pytest.fixture(scope='module')
def module_default_subnet(module_org, module_location):
    return entities.Subnet(location=[module_location], organization=[module_org]).create()


@pytest.fixture(scope='session')
def default_partitiontable():
    ptables = entities.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})
    if ptables:
        return ptables[0].read()


@pytest.fixture(scope='module')
def module_provisioningtemplate_default(module_org, module_location):
    provisioning_template = entities.ProvisioningTemplate().search(
        query={'search': f'name="{DEFAULT_TEMPLATE}"'}
    )
    provisioning_template = provisioning_template[0].read()
    provisioning_template.organization.append(module_org)
    provisioning_template.location.append(module_location)
    provisioning_template.update(['organization', 'location'])
    provisioning_template = entities.ProvisioningTemplate(id=provisioning_template.id).read()
    return provisioning_template


@pytest.fixture(scope='module')
def module_provisioningtemplate_pxe(module_org, module_location):
    pxe_template = entities.ProvisioningTemplate().search(
        query={'search': f'name="{DEFAULT_PXE_TEMPLATE}"'}
    )
    pxe_template = pxe_template[0].read()
    pxe_template.organization.append(module_org)
    pxe_template.location.append(module_location)
    pxe_template.update(['organization', 'location'])
    pxe_template = entities.ProvisioningTemplate(id=pxe_template.id).read()
    return pxe_template


@pytest.fixture(scope='session')
def default_architecture():
    arch = (
        entities.Architecture()
        .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]
        .read()
    )
    return arch


@pytest.fixture(scope='module')
def module_architecture():
    return entities.Architecture().create()


@pytest.fixture(scope='session')
def default_os(
    default_architecture,
    default_partitiontable,
    default_pxetemplate,
    request,
):
    """Returns an Operating System entity read from searching Redhat family

    Indirect parametrization should pass an operating system version string like 'RHEL 7.9'
    Default operating system will find the first RHEL6 or RHEL7 entity
    """
    os = getattr(request, 'param', None)
    if os is None:
        search_string = (
            f'name="RedHat" AND (major="{RHEL_6_MAJOR_VERSION}" '
            f'OR major="{RHEL_7_MAJOR_VERSION}")'
        )
    else:
        version = os.split(' ')[1].split('.')
        search_string = f'family="Redhat" AND major="{version[0]}" AND minor="{version[1]}"'
    os = entities.OperatingSystem().search(query={'search': search_string})[0].read()
    os.architecture.append(default_architecture)
    os.ptable.append(default_partitiontable)
    os.provisioning_template.append(default_pxetemplate)
    os.update(['architecture', 'ptable', 'provisioning_template'])
    os = entities.OperatingSystem(id=os.id).read()
    return os


@pytest.fixture(scope='module')
def module_os():
    return entities.OperatingSystem().create()


@pytest.fixture(scope='session')
def default_puppet_environment(module_org):
    environments = entities.Environment().search(
        query=dict(search=f'organization_id={module_org.id}')
    )
    if environments:
        return environments[0].read()


@pytest.fixture(scope='module')
def module_puppet_environment(module_org, module_location):
    environment = entities.Environment(
        organization=[module_org], location=[module_location]
    ).create()
    return entities.Environment(id=environment.id).read()


@pytest.fixture(scope='module')
def module_user(module_org, module_location):
    return entities.User(organization=[module_org], location=[module_location]).create()


# Compute resource - Libvirt entities
@pytest.fixture(scope="module")
def module_cr_libvirt(module_org, module_location):
    return entities.LibvirtComputeResource(
        organization=[module_org], location=[module_location]
    ).create()


@pytest.fixture(scope="module")
def module_libvirt_image(module_cr_libvirt):
    return entities.Image(compute_resource=module_cr_libvirt).create()


# Google Cloud Engine Entities


@pytest.fixture(scope='session')
def googleclient():
    gceclient = GoogleCloudSystem(
        project=settings.gce.project_id,
        zone=settings.gce.zone,
        file_path=download_gce_cert(),
        file_type='json',
    )
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
    cloudinit_uuid = googleclient.get_template('customcinit', project=settings.gce.project_id).uuid
    return cloudinit_uuid


@pytest.fixture(scope='module')
def module_gce_compute(module_org, module_location):
    gce_cr = entities.GCEComputeResource(
        name=gen_string('alphanumeric'),
        provider='GCE',
        email=settings.gce.client_email,
        key_path=settings.gce.cert_path,
        project=settings.gce.project_id,
        zone=settings.gce.zone,
        organization=[module_org],
        location=[module_location],
    ).create()
    return gce_cr


# Azure Entities


@pytest.fixture(scope='session')
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
def module_azurerm_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_byos_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates BYOS Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_BYOS_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_cloudimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates cloudinit image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_UD_IMG_URN,
        user_data=True,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_gallery_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates Shared Gallery Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_GALLERY_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_custom_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates Custom Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='session')
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
            "region_api": azurerm_settings['region'],
        },
    )
    yield azurermclient
    azurermclient.disconnect()


# Katello Entities


@pytest.fixture(scope='module')
def module_product(module_org):
    return entities.Product(organization=module_org).create()


@pytest.fixture(scope='module')
def module_cv(module_org):
    return entities.ContentView(organization=module_org).create()


@pytest.fixture(scope='module')
def module_published_cv(module_org):
    content_view = entities.ContentView(organization=module_org).create()
    content_view.publish()
    return content_view.read()


@pytest.fixture(scope='session')
def default_contentview(module_org):
    return entities.ContentView().search(
        query={'search': 'label=Default_Organization_View', 'organization_id': f'{module_org.id}'}
    )


@pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
@pytest.fixture(scope='module')
def module_cv_with_puppet_module(module_org):
    """Returns content view entity created by publish_puppet_module with chosen
    name and author of puppet module, custom puppet repository and organization.
    """
    return publish_puppet_module(
        [{'author': 'robottelo', 'name': 'generic_1'}],
        CUSTOM_PUPPET_REPO,
        organization_id=module_org.id,
    )


@pytest.fixture(scope='session')
def default_pxetemplate():
    pxe_template = entities.ProvisioningTemplate().search(query={'search': DEFAULT_PXE_TEMPLATE})
    return pxe_template[0].read()


@pytest.fixture(scope='module')
def module_env_search(module_org, module_location, module_cv_with_puppet_module):
    """Search for puppet environment according to the following criteria:
    Content view from module_cv_with_puppet_module and chosen organization.

    Returns the puppet environment with updated location.
    """
    env = (
        entities.Environment()
        .search(
            query={
                'search': f'content_view={module_cv_with_puppet_module.name} '
                f'and organization_id={module_org.id}'
            }
        )[0]
        .read()
    )
    env.location.append(module_location)
    env.update(['location'])
    return env


@pytest.fixture(scope='module')
def module_lce_search(module_org):
    """ Returns the Library lifecycle environment from chosen organization """
    return (
        entities.LifecycleEnvironment()
        .search(query={'search': f'name={ENVIRONMENT} and organization_id={module_org.id}'})[0]
        .read()
    )


@pytest.fixture(scope='module')
def module_puppet_classes(module_env_search):
    """Returns puppet class based on following criteria:
    Puppet environment from module_env_search and puppet class name. The name was set inside
    module_cv_with_puppet_module.
    """
    return entities.PuppetClass().search(
        query={'search': f'name ~ {"generic_1"} and environment = {module_env_search.name}'}
    )


# function scoped
@pytest.fixture(scope="function")
def function_role():
    return entities.Role().create()


@pytest.fixture(scope="function")
def setting_update(request):
    """
    This fixture is used to create an object of the provided settings parameter that we use in
    each test case to update their attributes and once the test case gets completed it helps to
    restore their default value
    """
    setting_object = entities.Setting().search(query={'search': f'name={request.param}'})[0]
    default_setting_value = setting_object.value
    yield setting_object
    setting_object.value = default_setting_value
    setting_object.update({'value'})


@pytest.fixture(scope="function")
def repo_setup():
    """
    This fixture is used to create an organization, product, repository, and lifecycle environment
    and once the test case gets completed then it performs the teardown of that.
    """
    repo_name = gen_string('alpha')
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    repo = entities.Repository(name=repo_name, product=product).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    details = {'org': org, 'product': product, 'repo': repo, 'lce': lce}
    yield details
    for property_name in ['lce', 'repo', 'product', 'org']:
        details[property_name].delete()


@pytest.fixture
def set_importing_org(request):
    """
    Sets same CV, product and repository in importing organization as exporting organization
    """
    product_name, repo_name, cv_name, mos = request.param
    importing_org = entities.Organization().create()
    importing_prod = entities.Product(organization=importing_org, name=product_name).create()

    importing_repo = entities.Repository(
        name=repo_name,
        mirror_on_sync=mos,
        download_policy='immediate',
        product=importing_prod,
    ).create()

    importing_cv = entities.ContentView(name=cv_name, organization=importing_org).create()
    importing_cv.repository = [importing_repo]
    importing_cv.update(['repository'])
    yield [importing_cv, importing_org]
    importing_cv.delete()
    importing_prod.delete()
    importing_org.delete()
