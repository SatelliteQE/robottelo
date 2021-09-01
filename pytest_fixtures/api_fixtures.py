# Module-wide Nailgun Entity Fixtures to be used by API, CLI and UI Tests
import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from wrapanapi import AzureSystem

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import publish_puppet_module
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import AZURERM_RHEL7_FT_BYOS_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_CUSTOM_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_GALLERY_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_IMG_URN
from robottelo.constants import AZURERM_RHEL7_UD_IMG_URN
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_PXE_TEMPLATE
from robottelo.constants import DEFAULT_TEMPLATE
from robottelo.constants import ENVIRONMENT
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.logging import logger


# Global Satellite Entities

if not settings.configured:
    settings.configure()


@pytest.fixture(scope='session')
def default_org():
    return entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]


@pytest.fixture(scope='session')
def default_location():
    return entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0]


@pytest.fixture(scope='function')
def function_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='class')
def class_org():
    org = entities.Organization().create()
    yield org
    org.delete()


@pytest.fixture(scope='module')
def module_manifest_org():
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    return org


@pytest.fixture(scope='module')
def module_gt_manifest_org():
    """Creates a new org and loads GT manifest in the new org"""
    org = entities.Organization().create()
    manifest = manifests.clone(org_environment_access=True, name='golden_ticket')
    manifests.upload_manifest_locked(org.id, manifest, interface=manifests.INTERFACE_CLI)
    org.manifest_filename = manifest.filename
    return org


@pytest.fixture(scope='module')
def module_location(module_org):
    return entities.Location(organization=[module_org]).create()


@pytest.fixture(scope='class')
def class_location(class_org):
    loc = entities.Location(organization=[class_org]).create()
    yield loc
    loc.delete()


@pytest.fixture(scope='session')
def default_lce():
    return entities.LifecycleEnvironment().search(query={'search': f'name="{ENVIRONMENT}"'})[0]


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='module')
def module_host():
    return entities.Host().create()


@pytest.fixture(scope='module')
def module_hostgroup():
    return entities.HostGroup().create()


@pytest.fixture(scope='class')
def class_hostgroup(class_org, class_location):
    """Create a hostgroup linked to specific org and location created at the class scope"""
    hostgroup = entities.HostGroup(organization=[class_org], location=[class_location]).create()
    yield hostgroup
    try:
        hostgroup.delete()
    except HTTPError:
        logger.exception('Exception while deleting class scope hostgroup entity in teardown')


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


@pytest.mark.vlan_networking
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


@pytest.fixture(scope='module')
def module_ak(module_lce, module_org):
    ak = entities.ActivationKey(
        environment=module_lce,
        organization=module_org,
    ).create()
    return ak


@pytest.fixture(scope='module')
def module_ak_with_cv(module_lce, module_org, module_promoted_cv):
    ak = entities.ActivationKey(
        content_view=module_promoted_cv,
        environment=module_lce,
        organization=module_org,
    ).create()
    return ak


@pytest.fixture(scope='session')
def default_architecture():
    arch = (
        entities.Architecture().search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0].read()
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


@pytest.fixture(scope='class')
def class_user_password():
    """Generate a random password for a user, and capture it so a test has access to it"""
    return gen_alphanumeric()


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
def gce_latest_rhel_uuid(googleclient):
    template_names = [img.name for img in googleclient.list_templates(True)]
    latest_rhel7_template = max(name for name in template_names if name.startswith('rhel-7'))
    latest_rhel7_uuid = googleclient.get_template(latest_rhel7_template, project='rhel-cloud').uuid
    return latest_rhel7_uuid


@pytest.fixture(scope='session')
def gce_custom_cloudinit_uuid(googleclient, gce_cert):
    cloudinit_uuid = googleclient.get_template('customcinit', project=gce_cert['project_id']).uuid
    return cloudinit_uuid


@pytest.fixture(scope='module')
def module_gce_compute(module_org, module_location, gce_cert):
    gce_cr = entities.GCEComputeResource(
        name=gen_string('alphanumeric'),
        provider='GCE',
        email=gce_cert['client_email'],
        key_path=settings.gce.cert_path,
        project=gce_cert['project_id'],
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
        'resource_group': settings.azurerm.resource_group,
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
            "resource_group": azurerm_settings['resource_group'],
            "template_container": None,
            "region_api": azurerm_settings['region'],
        },
    )
    yield azurermclient
    azurermclient.disconnect()


# Katello Entities


@pytest.fixture(scope='module')
def module_activation_key(module_org):
    return entities.ActivationKey(organization=module_org).create()


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


@pytest.fixture(scope="module")
def module_promoted_cv(module_lce, module_published_cv):
    """ Promote published content view """
    promote(module_published_cv.version[0], environment_id=module_lce.id)
    return module_published_cv


@pytest.fixture(scope='module')
def default_contentview(module_org):
    return entities.ContentView(organization=module_org, name=DEFAULT_CV).search()


@pytest.fixture(scope='module')
def module_ak_cv_lce(module_org, module_lce, module_published_cv):
    """Module Activation key with CV promoted to LCE"""
    promote(module_published_cv.version[0], module_lce.id)
    module_published_cv = module_published_cv.read()
    module_ak_cv_lce = entities.ActivationKey(
        content_view=module_published_cv,
        environment=module_lce,
        organization=module_org,
    ).create()
    return module_ak_cv_lce


@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
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
def module_env():
    return entities.Environment().create()


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
def module_lce_library(module_org):
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


@pytest.fixture(scope='module')
def rh_repo_gt_manifest(module_gt_manifest_org):
    """Use GT manifest org, creates RH tools repo, syncs and returns RH repo."""
    # enable rhel repo and return its ID
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_gt_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    # Sync step because repo is not synced by default
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


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
    if default_setting_value is None:
        default_setting_value = ''
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
