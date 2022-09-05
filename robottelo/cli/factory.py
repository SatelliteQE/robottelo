"""
Factory object creation for all CLI methods
"""
import datetime
import os
import pprint
import random
from os import chmod
from tempfile import mkstemp
from time import sleep

from fauxfactory import gen_alphanumeric
from fauxfactory import gen_choice
from fauxfactory import gen_integer
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_netmask
from fauxfactory import gen_string
from fauxfactory import gen_url

from robottelo import constants
from robottelo import manifests
from robottelo import ssh
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.architecture import Architecture
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.content_credentials import ContentCredential
from robottelo.cli.contentview import ContentView
from robottelo.cli.contentview import ContentViewFilter
from robottelo.cli.contentview import ContentViewFilterRule
from robottelo.cli.discoveryrule import DiscoveryRule
from robottelo.cli.domain import Domain
from robottelo.cli.environment import Environment
from robottelo.cli.filter import Filter
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.http_proxy import HttpProxy
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.job_template import JobTemplate
from robottelo.cli.ldapauthsource import LDAPAuthSource
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.medium import Medium
from robottelo.cli.model import Model
from robottelo.cli.operatingsys import OperatingSys
from robottelo.cli.org import Org
from robottelo.cli.partitiontable import PartitionTable
from robottelo.cli.product import Product
from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.cli.proxy import Proxy
from robottelo.cli.realm import Realm
from robottelo.cli.report_template import ReportTemplate
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.role import Role
from robottelo.cli.scap_policy import Scappolicy
from robottelo.cli.scap_tailoring_files import TailoringFiles
from robottelo.cli.scapcontent import Scapcontent
from robottelo.cli.subnet import Subnet
from robottelo.cli.subscription import Subscription
from robottelo.cli.syncplan import SyncPlan
from robottelo.cli.template import Template
from robottelo.cli.template_input import TemplateInput
from robottelo.cli.user import User
from robottelo.cli.usergroup import UserGroup
from robottelo.cli.usergroup import UserGroupExternal
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.datafactory import valid_cron_expressions
from robottelo.decorators import cacheable
from robottelo.helpers import default_url_on_new_port
from robottelo.helpers import get_available_capsule_port
from robottelo.logging import logger


ORG_KEYS = ['organization', 'organization-id', 'organization-label']
CONTENT_VIEW_KEYS = ['content-view', 'content-view-id']
LIFECYCLE_KEYS = ['lifecycle-environment', 'lifecycle-environment-id']


class CLIFactoryError(Exception):
    """Indicates an error occurred while creating an entity using hammer"""


def create_object(cli_object, options, values):
    """
    Creates <object> with dictionary of arguments.

    :param cli_object: A valid CLI object.
    :param dict options: The default options accepted by the cli_object
        create
    :param dict values: Custom values to override default ones.
    :raise robottelo.cli.factory.CLIFactoryError: Raise an exception if object
        cannot be created.
    :rtype: dict
    :return: A dictionary representing the newly created resource.

    """
    if values:
        diff = set(values.keys()).difference(set(options.keys()))
        if diff:
            logger.debug(
                "Option(s) {} not supported by CLI factory. Please check for "
                "a typo or update default options".format(diff)
            )
        for key in set(options.keys()).intersection(set(values.keys())):
            options[key] = values[key]

    try:
        result = cli_object.create(options)
    except CLIReturnCodeError as err:
        # If the object is not created, raise exception, stop the show.
        raise CLIFactoryError(
            'Failed to create {} with data:\n{}\n{}'.format(
                cli_object.__name__, pprint.pformat(options, indent=2), err.msg
            )
        )

    # Sometimes we get a list with a dictionary and not
    # a dictionary.
    if type(result) is list and len(result) > 0:
        result = result[0]

    return result


def _entity_with_credentials(credentials, cli_entity_cls):
    """Create entity class using credentials. If credentials is None will
    return cli_entity_cls itself

    :param credentials: tuple (login, password)
    :param cli_entity_cls: Cli Entity Class
    :return: Cli Entity Class
    """
    if credentials is not None:
        cli_entity_cls = cli_entity_cls.with_user(*credentials)
    return cli_entity_cls


@cacheable
def make_activation_key(options=None):
    """Creates an Activation Key

    :param options: Check options using `hammer activation-key create --help` on satellite.

    :returns ActivationKey object
    """
    # Organization Name, Label or ID is a required field.
    if (
        not options
        or not options.get('organization')
        and not options.get('organization-label')
        and not options.get('organization-id')
    ):
        raise CLIFactoryError('Please provide a valid Organization.')

    args = {
        'content-view': None,
        'content-view-id': None,
        'description': None,
        'lifecycle-environment': None,
        'lifecycle-environment-id': None,
        'max-hosts': None,
        'name': gen_alphanumeric(),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'unlimited-hosts': None,
        'service-level': None,
        'purpose-role': None,
        'purpose-usage': None,
        'purpose-addons': None,
    }

    return create_object(ActivationKey, args, options)


@cacheable
def make_architecture(options=None):
    """Creates an Architecture

    :param options: Check options using `hammer architecture create --help` on satellite.

    :returns Architecture object
    """
    args = {'name': gen_alphanumeric(), 'operatingsystem-ids': None}

    return create_object(Architecture, args, options)


@cacheable
def make_content_view(options=None):
    """Creates a Content View

    :param options: Check options using `hammer content-view create --help` on satellite.

    :returns ContentView object
    """
    return make_content_view_with_credentials(options)


def make_content_view_with_credentials(options=None, credentials=None):
    """Helper function to create CV with credentials

    If credentials is None, the default credentials in robottelo.properties will be used.
    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    args = {
        'component-ids': None,
        'composite': False,
        'description': None,
        'import-only': False,
        'label': None,
        'name': gen_string('alpha', 10),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'product': None,
        'product-id': None,
        'repositories': None,
        'repository-ids': None,
    }

    cv_cls = _entity_with_credentials(credentials, ContentView)
    return create_object(cv_cls, args, options)


@cacheable
def make_content_view_filter(options=None):
    """Creates a Content View Filter

    :param options: Check options using `hammer content-view filter create --help` on satellite.

    :returns ContentViewFilter object
    """

    args = {
        'content-view': None,
        'content-view-id': None,
        'description': None,
        'inclusion': None,
        'name': gen_string('alpha', 10),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'original-packages': None,
        'repositories': None,
        'repository-ids': None,
        'type': None,
    }

    return create_object(ContentViewFilter, args, options)


@cacheable
def make_content_view_filter_rule(options=None):
    """Creates a Content View Filter Rule

    :param options: Check options using `hammer content-view filter rule create --help` on
        satellite.

    :returns ContentViewFilterRule object
    """

    args = {
        'content-view': None,
        'content-view-filter': None,
        'content-view-filter-id': None,
        'content-view-id': None,
        'date-type': None,
        'end-date': None,
        'errata-id': None,
        'errata-ids': None,
        'max-version': None,
        'min-version': None,
        'name': None,
        'names': None,
        'start-date': None,
        'types': None,
        'version': None,
    }

    return create_object(ContentViewFilterRule, args, options)


@cacheable
def make_discoveryrule(options=None):
    """Creates a Discovery Rule

    :param options: Check options using `hammer discovery-rule create --help` on satellite.

    :returns DiscoveryRule object
    """

    # Organizations, Locations, search query, hostgroup are required fields.
    if not options:
        raise CLIFactoryError('Please provide required parameters')
    # Organizations fields is required
    if not any(options.get(key) for key in ['organizations', 'organization-ids']):
        raise CLIFactoryError('Please provide a valid organization field.')
    # Locations field is required
    if not any(options.get(key) for key in ['locations', 'location-ids']):
        raise CLIFactoryError('Please provide a valid location field.')
    # search query is required
    if not options.get('search'):
        raise CLIFactoryError('Please provider a valid search query')
    # hostgroup is required
    if not any(options.get(key) for key in ['hostgroup', 'hostgroup-id']):
        raise CLIFactoryError('Please provider a valid hostgroup')

    args = {
        'enabled': None,
        'hostgroup': None,
        'hostgroup-id': None,
        'hostgroup-title': None,
        'hostname': None,
        'hosts-limit': None,
        'location-ids': None,
        'locations': None,
        'max-count': None,
        'name': gen_alphanumeric(),
        'organizations': None,
        'organization-ids': None,
        'priority': None,
        'search': None,
    }

    return create_object(DiscoveryRule, args, options)


@cacheable
def make_content_credential(options=None):
    """Creates a content credential.

    In Satellite 6.8, only gpg_key option is supported.

    :param options: Check options using `hammer content-credential create --help` on satellite.

    :returns ContentCredential object
    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    # Create a fake gpg key file if none was provided
    if not options.get('path'):
        (_, key_filename) = mkstemp(text=True)
        os.chmod(key_filename, 0o700)
        with open(key_filename, 'w') as gpg_key_file:
            gpg_key_file.write(gen_alphanumeric(gen_integer(20, 50)))
    else:
        # If the key is provided get its local path and remove it from options
        # to not override the remote path
        key_filename = options.pop('path')

    args = {
        'path': f'/tmp/{gen_alphanumeric()}',
        'content-type': 'gpg_key',
        'name': gen_alphanumeric(),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
    }

    # Upload file to server
    ssh.get_client().put(key_filename, args['path'])

    return create_object(ContentCredential, args, options)


@cacheable
def make_location(options=None):
    """Creates a Location

    :param options: Check options using `hammer location create --help` on satellite.

    :returns Location object
    """
    args = {
        'compute-resource-ids': None,
        'compute-resources': None,
        'description': None,
        'domain-ids': None,
        'domains': None,
        'environment-ids': None,
        'environments': None,
        'puppet-environment-ids': None,
        'puppet-environments': None,
        'hostgroup-ids': None,
        'hostgroups': None,
        'medium-ids': None,
        'name': gen_alphanumeric(),
        'parent-id': None,
        'provisioning-template-ids': None,
        'provisioning-templates': None,
        'realm-ids': None,
        'realms': None,
        'smart-proxy-ids': None,
        'smart-proxies': None,
        'subnet-ids': None,
        'subnets': None,
        'user-ids': None,
        'users': None,
    }

    return create_object(Location, args, options)


@cacheable
def make_model(options=None):
    """Creates a Hardware Model

    :param options: Check options using `hammer model create --help` on satellite.

    :returns Model object
    """
    args = {'hardware-model': None, 'info': None, 'name': gen_alphanumeric(), 'vendor-class': None}

    return create_object(Model, args, options)


@cacheable
def make_partition_table(options=None):
    """Creates a Partition Table

    :param options: Check options using `hammer partition-table create --help` on satellite.

    :returns PartitionTable object
    """
    if options is None:
        options = {}
    (_, layout) = mkstemp(text=True)
    os.chmod(layout, 0o700)
    with open(layout, 'w') as ptable:
        ptable.write(options.get('content', 'default ptable content'))

    args = {
        'file': f'/tmp/{gen_alphanumeric()}',
        'location-ids': None,
        'locations': None,
        'name': gen_alphanumeric(),
        'operatingsystem-ids': None,
        'operatingsystems': None,
        'organization-ids': None,
        'organizations': None,
        'os-family': random.choice(constants.OPERATING_SYSTEMS),
    }

    # Upload file to server
    ssh.get_client().put(layout, args['file'])

    return create_object(PartitionTable, args, options)


@cacheable
def make_product(options=None):
    """Creates a Product

    :param options: Check options using `hammer product create --help` on satellite.

    :returns Product object
    """
    return make_product_with_credentials(options)


def make_product_with_credentials(options=None, credentials=None):
    """Helper function to create product with credentials"""
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    args = {
        'description': gen_string('alpha', 20),
        'gpg-key': None,
        'gpg-key-id': None,
        'label': gen_string('alpha', 20),
        'name': gen_string('alpha', 20),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'sync-plan': None,
        'sync-plan-id': None,
    }
    product_cls = _entity_with_credentials(credentials, Product)
    return create_object(product_cls, args, options)


def make_product_wait(options=None, wait_for=5):
    """Wrapper function for make_product to make it wait before erroring out.

    This is a temporary workaround for BZ#1332650: Sometimes cli product
    create errors for no reason when there are multiple product creation
    requests at the sametime although the product entities are created.  This
    workaround will attempt to wait for 5 seconds and query the
    product again to make sure it is actually created.  If it is not found,
    it will fail and stop.

    Note: This wrapper method is created instead of patching make_product
    because this issue does not happen for all entities and this workaround
    should be removed once the root cause is identified/fixed.
    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')
    options['name'] = options.get('name', gen_string('alpha'))
    try:
        product = make_product(options)
    except CLIFactoryError as err:
        sleep(wait_for)
        try:
            product = Product.info(
                {'name': options.get('name'), 'organization-id': options.get('organization-id')}
            )
        except CLIReturnCodeError:
            raise err
        if not product:
            raise err
    return product


@cacheable
def make_proxy(options=None):
    """Creates a Proxy

    :param options: Check options using `hammer proxy create --help` on satellite.

    :returns Proxy object
    """
    args = {'name': gen_alphanumeric()}

    if options is None or 'url' not in options:
        newport = get_available_capsule_port()
        try:
            with default_url_on_new_port(9090, newport) as url:
                args['url'] = url
                return create_object(Proxy, args, options)
        except CapsuleTunnelError as err:
            raise CLIFactoryError(f'Failed to create ssh tunnel: {err}')
    args['url'] = options['url']
    return create_object(Proxy, args, options)


@cacheable
def make_repository(options=None):
    """Creates a Repository

    :param options: Check options using `hammer repository create --help` on satellite.

    :returns Repository object
    """
    return make_repository_with_credentials(options)


def make_repository_with_credentials(options=None, credentials=None):
    """Helper function to create Repository with credentials"""
    # Product ID is a required field.
    if not options or not options.get('product-id'):
        raise CLIFactoryError('Please provide a valid Product ID.')

    args = {
        'checksum-type': None,
        'content-type': 'yum',
        'include-tags': None,
        'docker-upstream-name': None,
        'download-policy': None,
        'gpg-key': None,
        'gpg-key-id': None,
        'ignorable-content': None,
        'label': None,
        'mirroring-policy': None,
        'name': gen_string('alpha', 15),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'product': None,
        'product-id': None,
        'publish-via-http': 'true',
        'http-proxy': None,
        'http-proxy-id': None,
        'http-proxy-policy': None,
        'ansible-collection-requirements': None,
        'ansible-collection-requirements-file': None,
        'ansible-collection-auth-token': None,
        'ansible-collection-auth-url': None,
        'url': settings.repos.yum_1.url,
        'upstream-username': None,
        'upstream-password': None,
    }
    repo_cls = _entity_with_credentials(credentials, Repository)
    return create_object(repo_cls, args, options)


@cacheable
def make_role(options=None):
    """Creates a Role

    :param options: Check options using `hammer role create --help` on satellite.

    :returns Role object
    """
    # Assigning default values for attributes
    args = {'name': gen_alphanumeric(6)}

    return create_object(Role, args, options)


@cacheable
def make_filter(options=None):
    """Creates a Role Filter

    :param options: Check options using `hammer filter create --help` on satellite.

    :returns Role object
    """
    args = {
        'location-ids': None,
        'locations': None,
        'organization-ids': None,
        'organizations': None,
        'override': None,
        'permission-ids': None,
        'permissions': None,
        'role': None,
        'role-id': None,
        'search': None,
    }

    # Role and permissions are required fields.
    if not options:
        raise CLIFactoryError('Please provide required parameters')

    # Do we have at least one role field?
    if not any(options.get(key) for key in ['role', 'role-id']):
        raise CLIFactoryError('Please provide a valid role field.')

    # Do we have at least one permissions field?
    if not any(options.get(key) for key in ['permissions', 'permission-ids']):
        raise CLIFactoryError('Please provide a valid permissions field.')

    return create_object(Filter, args, options)


@cacheable
def make_scap_policy(options=None):
    """Creates a Scap Policy

    :param options: Check options using `hammer policy create --help` on satellite.

    :returns Scappolicy object
    """
    # Assigning default values for attributes
    # SCAP ID and SCAP profile ID is a required field.
    if (
        not options
        and not options.get('scap-content-id')
        and not options.get('scap-content-profile-id')
        and not options.get('period')
        and not options.get('deploy-by')
    ):
        raise CLIFactoryError(
            'Please provide a valid SCAP ID or SCAP Profile ID or Period or Deploy by option'
        )
    args = {
        'description': None,
        'scap-content-id': None,
        'scap-content-profile-id': None,
        'deploy-by': None,
        'period': None,
        'weekday': None,
        'day-of-month': None,
        'cron-line': None,
        'hostgroup-ids': None,
        'hostgroups': None,
        'locations': None,
        'organizations': None,
        'tailoring-file': None,
        'tailoring-file-id': None,
        'tailoring-file-profile-id': None,
        'location-ids': None,
        'name': gen_alphanumeric().lower(),
        'organization-ids': None,
    }

    return create_object(Scappolicy, args, options)


@cacheable
def make_subnet(options=None):
    """Creates a Subnet

    :param options: Check options using `hammer subnet create --help` on satellite.

    :returns Subnet object
    """
    args = {
        'boot-mode': None,
        'dhcp-id': None,
        'dns-id': None,
        'dns-primary': None,
        'dns-secondary': None,
        'domain-ids': None,
        'domains': None,
        'from': None,
        'gateway': None,
        'ipam': None,
        'location-ids': None,
        'locations': None,
        'mask': gen_netmask(),
        'name': gen_alphanumeric(8),
        'network': gen_ipaddr(ip3=True),
        'organization-ids': None,
        'organizations': None,
        'tftp-id': None,
        'to': None,
        'vlanid': None,
    }

    return create_object(Subnet, args, options)


@cacheable
def make_sync_plan(options=None):
    """Creates a Sync Plan

    :param options: Check options using `hammer sync-plan create --help` on satellite.

    :returns SyncPlan object
    """
    # Organization ID is a required field.
    if not options or not options.get('organization-id'):
        raise CLIFactoryError('Please provide a valid ORG ID.')

    args = {
        'description': gen_string('alpha', 20),
        'enabled': 'true',
        'interval': random.choice(list(constants.SYNC_INTERVAL.values())),
        'name': gen_string('alpha', 20),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'sync-date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cron-expression': None,
    }
    if options.get('interval', args['interval']) == constants.SYNC_INTERVAL[
        'custom'
    ] and not options.get('cron-expression'):
        args['cron-expression'] = gen_choice(valid_cron_expressions())
    return create_object(SyncPlan, args, options)


@cacheable
def make_host(options=None):
    """Creates a Host

    :param options: Check options using `hammer host create --help` on satellite.

    :returns Host object
    """
    args = {
        'architecture': None,
        'architecture-id': None,
        'ask-root-password': None,
        'autoheal': None,
        'build': None,
        'comment': None,
        'compute-attributes': None,
        'compute-profile': None,
        'compute-profile-id': None,
        'compute-resource': None,
        'compute-resource-id': None,
        'content-source-id': None,
        'content-view': None,
        'content-view-id': None,
        'domain': None,
        'domain-id': None,
        'enabled': None,
        'environment': None,
        'environment-id': None,
        'hostgroup': None,
        'hostgroup-id': None,
        'hostgroup-title': None,
        'hypervisor-guest-uuids': None,
        'image': None,
        'image-id': None,
        'interface': None,
        'ip': gen_ipaddr(),
        'kickstart-repository-id': None,
        'lifecycle-environment': None,
        'lifecycle-environment-id': None,
        'location': None,
        'location-id': None,
        'mac': gen_mac(multicast=False),
        'managed': None,
        'medium': None,
        'medium-id': None,
        'model': None,
        'model-id': None,
        'name': gen_string('alpha', 10),
        'operatingsystem': None,
        'operatingsystem-id': None,
        'openscap-proxy-id': None,
        'organization': None,
        'organization-id': None,
        'overwrite': None,
        'owner': None,
        'owner-id': None,
        'owner-type': None,
        'parameters': None,
        'partition-table': None,
        'partition-table-id': None,
        'progress-report-id': None,
        'provision-method': None,
        'puppet-ca-proxy': None,
        'puppet-ca-proxy-id': None,
        'puppet-class-ids': None,
        'puppet-classes': None,
        'puppet-proxy': None,
        'puppet-proxy-id': None,
        'pxe-loader': None,
        'realm': None,
        'realm-id': None,
        'root-password': gen_string('alpha', 8),
        'service-level': None,
        'subnet': None,
        'subnet-id': None,
        'volume': None,
    }

    return create_object(Host, args, options)


@cacheable
def make_fake_host(options=None):
    """Wrapper function for make_host to pass all required options for creation
    of a fake host
    """
    if options is None:
        options = {}

    # Try to use default Satellite entities, otherwise create them if they were
    # not passed or defined previously
    if not options.get('organization') and not options.get('organization-id'):
        try:
            options['organization-id'] = Org.info({'name': constants.DEFAULT_ORG})['id']
        except CLIReturnCodeError:
            options['organization-id'] = make_org()['id']
    if not options.get('location') and not options.get('location-id'):
        try:
            options['location-id'] = Location.info({'name': constants.DEFAULT_LOC})['id']
        except CLIReturnCodeError:
            options['location-id'] = make_location()['id']
    if not options.get('domain') and not options.get('domain-id'):
        options['domain-id'] = make_domain(
            {
                'location-ids': options.get('location-id'),
                'locations': options.get('location'),
                'organization-ids': options.get('organization-id'),
                'organizations': options.get('organization'),
            }
        )['id']
    if not options.get('architecture') and not options.get('architecture-id'):
        try:
            options['architecture-id'] = Architecture.info(
                {'name': constants.DEFAULT_ARCHITECTURE}
            )['id']
        except CLIReturnCodeError:
            options['architecture-id'] = make_architecture()['id']
    if not options.get('operatingsystem') and not options.get('operatingsystem-id'):
        try:
            options['operatingsystem-id'] = OperatingSys.list(
                {'search': 'name="RedHat" AND (major="6" OR major="7")'}
            )[0]['id']
        except IndexError:
            options['operatingsystem-id'] = make_os(
                {
                    'architecture-ids': options.get('architecture-id'),
                    'architectures': options.get('architecture'),
                    'partition-table-ids': options.get('partition-table-id'),
                    'partition-tables': options.get('partition-table'),
                }
            )['id']
    if not options.get('partition-table') and not options.get('partition-table-id'):
        try:
            options['partition-table-id'] = PartitionTable.list(
                {
                    'operatingsystem': options.get('operatingsystem'),
                    'operatingsystem-id': options.get('operatingsystem-id'),
                }
            )[0]['id']
        except IndexError:
            options['partition-table-id'] = make_partition_table(
                {
                    'location-ids': options.get('location-id'),
                    'locations': options.get('location'),
                    'operatingsystem-ids': options.get('operatingsystem-id'),
                    'organization-ids': options.get('organization-id'),
                    'organizations': options.get('organization'),
                }
            )['id']

    # Finally, create a new medium (if none was passed)
    if not options.get('medium') and not options.get('medium-id'):
        options['medium-id'] = make_medium(
            {
                'location-ids': options.get('location-id'),
                'locations': options.get('location'),
                'operatingsystems': options.get('operatingsystem'),
                'operatingsystem-ids': options.get('operatingsystem-id'),
                'organization-ids': options.get('organization-id'),
                'organizations': options.get('organization'),
            }
        )['id']

    return make_host(options)


@cacheable
def make_host_collection(options=None):
    """Creates a Host Collection

    :param options: Check options using `hammer host-collection create  --help` on satellite.

    :returns HostCollection object
    """
    # Assigning default values for attributes
    args = {
        'description': None,
        'host-collection-ids': None,
        'hosts': None,
        'max-hosts': None,
        'name': gen_string('alpha', 15),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'unlimited-hosts': None,
    }

    return create_object(HostCollection, args, options)


@cacheable
def make_job_invocation(options=None):
    """Creates a Job Invocation

    :param options: Check options using `hammer job-invocation create --help` on satellite.

    :returns JobInvocation object
    """
    return make_job_invocation_with_credentials(options)


def make_job_invocation_with_credentials(options=None, credentials=None):
    """Helper function to create Job Invocation with credentials"""

    args = {
        'async': None,
        'bookmark': None,
        'bookmark-id': None,
        'concurrency-level': None,
        'cron-line': None,
        'description-format': None,
        'dynamic': None,
        'effective-user': None,
        'end-time': None,
        'input-files': None,
        'inputs': None,
        'job-template': None,
        'job-template-id': None,
        'max-iteration': None,
        'search-query': None,
        'start-at': None,
        'start-before': None,
        'time-span': None,
    }

    jinv_cls = _entity_with_credentials(credentials, JobInvocation)
    return create_object(jinv_cls, args, options)


@cacheable
def make_job_template(options=None):
    """Creates a Job Template

    :param options: Check options using `hammer job-template create --help` on satellite.

    :returns JobTemplate object
    """
    args = {
        'audit-comment': None,
        'current-user': None,
        'description-format': None,
        'file': None,
        'job-category': 'Miscellaneous',
        'location-ids': None,
        'locations': None,
        'name': None,
        'organization-ids': None,
        'organizations': None,
        'overridable': None,
        'provider-type': 'SSH',
        'snippet': None,
        'value': None,
    }

    return create_object(JobTemplate, args, options)


@cacheable
def make_user(options=None):
    """Creates a User

    :param options: Check options using `hammer user create --help` on satellite.

    :returns User object
    """
    login = gen_alphanumeric(6)

    # Assigning default values for attributes
    args = {
        'admin': None,
        'auth-source-id': 1,
        'default-location-id': None,
        'default-organization-id': None,
        'description': None,
        'firstname': gen_alphanumeric(),
        'lastname': gen_alphanumeric(),
        'location-ids': None,
        'login': login,
        'mail': f'{login}@example.com',
        'organization-ids': None,
        'password': gen_alphanumeric(),
        'timezone': None,
    }
    logger.debug(
        'User "{}" password not provided {} was generated'.format(args['login'], args['password'])
    )

    return create_object(User, args, options)


@cacheable
def make_usergroup(options=None):
    """Creates a User Group

    :param options: Check options using `hammer user-group create --help` on satellite.

    :returns UserGroup object
    """
    # Assigning default values for attributes
    args = {
        'admin': None,
        'name': gen_alphanumeric(),
        'role-ids': None,
        'roles': None,
        'user-group-ids': None,
        'user-groups': None,
        'user-ids': None,
        'users': None,
    }

    return create_object(UserGroup, args, options)


@cacheable
def make_usergroup_external(options=None):
    """Creates an External User Group

    :param options: Check options using `hammer user-group external create --help` on satellite.

    :returns UserGroupExternal object
    """
    # UserGroup Name or ID is a required field.
    if not options or not options.get('user-group') and not options.get('user-group-id'):
        raise CLIFactoryError('Please provide a valid UserGroup.')

    # Assigning default values for attributes
    args = {
        'auth-source-id': 1,
        'name': gen_alphanumeric(8),
        'user-group': None,
        'user-group-id': None,
    }

    return create_object(UserGroupExternal, args, options)


@cacheable
def make_ldap_auth_source(options=None):
    """Creates an LDAP Auth Source

    :param options: Check options using `hammer auth-source ldap create --help` on satellite.

    :returns LDAPAuthSource object
    """
    # Assigning default values for attributes
    args = {
        'account': None,
        'account-password': None,
        'attr-firstname': None,
        'attr-lastname': None,
        'attr-login': None,
        'attr-mail': None,
        'attr-photo': None,
        'base-dn': None,
        'groups-base': None,
        'host': None,
        'ldap-filter': None,
        'location-ids': None,
        'locations': None,
        'name': gen_alphanumeric(),
        'onthefly-register': None,
        'organization-ids': None,
        'organizations': None,
        'port': None,
        'server-type': None,
        'tls': None,
        'usergroup-sync': None,
    }

    return create_object(LDAPAuthSource, args, options)


@cacheable
def make_compute_resource(options=None):
    """Creates a Compute Resource

    :param options: Check options using `hammer compute-resource create --help` on satellite.

    :returns ComputeResource object
    """
    args = {
        'caching-enabled': None,
        'datacenter': None,
        'description': None,
        'display-type': None,
        'domain': None,
        'location': None,
        'location-id': None,
        'location-ids': None,
        'location-title': None,
        'location-titles': None,
        'locations': None,
        'name': gen_alphanumeric(8),
        'organization': None,
        'organization-id': None,
        'organization-ids': None,
        'organization-title': None,
        'organization-titles': None,
        'organizations': None,
        'ovirt-quota': None,
        'password': None,
        'project-domain-id': None,
        'project-domain-name': None,
        'provider': None,
        'public-key': None,
        'public-key-path': None,
        'region': None,
        'server': None,
        'set-console-password': None,
        'tenant': None,
        'url': None,
        'use-v4': None,
        'user': None,
        'uuid': None,
    }

    if options is None:
        options = {}

    if options.get('provider') is None:
        options['provider'] = constants.FOREMAN_PROVIDERS['libvirt']
        if options.get('url') is None:
            options['url'] = 'qemu+tcp://localhost:16509/system'

    return create_object(ComputeResource, args, options)


@cacheable
def make_org(options=None):
    """Creates an Organization

    :param options: Check options using `hammer organization create --help` on satellite.

    :returns Organization object
    """
    return make_org_with_credentials(options)


def make_org_with_credentials(options=None, credentials=None):
    """Helper function to create organization with credentials"""
    # Assigning default values for attributes
    args = {
        'compute-resource-ids': None,
        'compute-resources': None,
        'provisioning-template-ids': None,
        'provisioning-templates': None,
        'description': None,
        'domain-ids': None,
        'environment-ids': None,
        'environments': None,
        'hostgroup-ids': None,
        'hostgroups': None,
        'label': None,
        'media-ids': None,
        'media': None,
        'name': gen_alphanumeric(6),
        'realm-ids': None,
        'realms': None,
        'smart-proxy-ids': None,
        'smart-proxies': None,
        'subnet-ids': None,
        'subnets': None,
        'user-ids': None,
        'users': None,
    }
    org_cls = _entity_with_credentials(credentials, Org)
    return create_object(org_cls, args, options)


@cacheable
def make_realm(options=None):
    """Creates a REALM

    :param options: Check options using `hammer realm create --help` on satellite.

    :returns Realm object
    """
    # Assigning default values for attributes
    args = {
        'location-ids': None,
        'locations': None,
        'name': gen_alphanumeric(6),
        'organization-ids': None,
        'organizations': None,
        'realm-proxy-id': None,
        'realm-type': None,
    }

    return create_object(Realm, args, options)


@cacheable
def make_report_template(options=None):
    """Creates a Report Template

    :param options: Check options using `hammer report-template create --help` on satellite.

    :returns ReportTemplate object
    """
    if options is not None and 'content' in options.keys():
        content = options.pop('content')
    else:
        content = gen_alphanumeric()

    args = {
        'audit-comment': None,
        'default': None,
        'file': content,
        'interactive': None,
        'location': None,
        'location-id': None,
        'location-ids': None,
        'location-title': None,
        'location-titles': None,
        'locations': None,
        'locked': None,
        'name': gen_alphanumeric(10),
        'organization': None,
        'organization-id': None,
        'organization-ids': None,
        'organization-title': None,
        'organization-titles': None,
        'organizations': None,
        'snippet': None,
    }
    return create_object(ReportTemplate, args, options)


@cacheable
def make_os(options=None):
    """Creates an Operating System

    :param options: Check options using `hammer os create --help` on satellite.

    :returns OperatingSys object
    """
    # Assigning default values for attributes
    args = {
        'architecture-ids': None,
        'architectures': None,
        'provisioning-template-ids': None,
        'provisioning-templates': None,
        'description': None,
        'family': None,
        'major': random.randint(0, 10),
        'media': None,
        'medium-ids': None,
        'minor': random.randint(0, 10),
        'name': gen_alphanumeric(6),
        'partition-table-ids': None,
        'partition-tables': None,
        'password-hash': None,
        'release-name': None,
    }

    return create_object(OperatingSys, args, options)


@cacheable
def make_scapcontent(options=None):
    """Creates Scap Content

    :param options: Check options using `hammer scap-content create --help` on satellite.

    :returns ScapContent object
    """
    # Assigning default values for attributes
    args = {
        'scap-file': None,
        'original-filename': None,
        'location-ids': None,
        'locations': None,
        'title': gen_alphanumeric().lower(),
        'organization-ids': None,
        'organizations': None,
    }

    return create_object(Scapcontent, args, options)


@cacheable
def make_domain(options=None):
    """Creates a Domain

    :param options: Check options using `hammer domain create --help` on satellite.

    :returns Domain object
    """
    # Assigning default values for attributes
    args = {
        'description': None,
        'dns-id': None,
        'location-ids': None,
        'locations': None,
        'name': gen_alphanumeric().lower(),
        'organization-ids': None,
        'organizations': None,
    }

    return create_object(Domain, args, options)


@cacheable
def make_hostgroup(options=None):
    """Creates a Hostgroup

    :param options: Check options using `hammer hostgroup create --help` on satellite.

    :returns Hostgroup object
    """
    # Assigning default values for attributes
    args = {
        'architecture': None,
        'architecture-id': None,
        'compute-profile': None,
        'compute-profile-id': None,
        'config-group-ids': None,
        'config-groups': None,
        'content-source-id': None,
        'content-source': None,
        'content-view': None,
        'content-view-id': None,
        'domain': None,
        'domain-id': None,
        'environment': None,
        'puppet-environment': None,
        'environment-id': None,
        'puppet-environment-id': None,
        'locations': None,
        'location-ids': None,
        'kickstart-repository-id': None,
        'lifecycle-environment': None,
        'lifecycle-environment-id': None,
        'lifecycle-environment-organization-id': None,
        'medium': None,
        'medium-id': None,
        'name': gen_alphanumeric(6),
        'operatingsystem': None,
        'operatingsystem-id': None,
        'organizations': None,
        'organization-titles': None,
        'organization-ids': None,
        'parent': None,
        'parent-id': None,
        'parent-title': None,
        'partition-table': None,
        'partition-table-id': None,
        'puppet-ca-proxy': None,
        'puppet-ca-proxy-id': None,
        'puppet-class-ids': None,
        'puppet-classes': None,
        'puppet-proxy': None,
        'puppet-proxy-id': None,
        'pxe-loader': None,
        'query-organization': None,
        'query-organization-id': None,
        'query-organization-label': None,
        'realm': None,
        'realm-id': None,
        'root-password': None,
        'subnet': None,
        'subnet-id': None,
    }

    return create_object(HostGroup, args, options)


@cacheable
def make_medium(options=None):
    """Creates a Medium

    :param options: Check options using `hammer medium create --help` on satellite.

    :returns Medium object
    """
    # Assigning default values for attributes
    args = {
        'location-ids': None,
        'locations': None,
        'name': gen_alphanumeric(6),
        'operatingsystem-ids': None,
        'operatingsystems': None,
        'organization-ids': None,
        'organizations': None,
        'os-family': None,
        'path': 'http://{}'.format(gen_string('alpha', 6)),
    }

    return create_object(Medium, args, options)


@cacheable
def make_environment(options=None):
    """Creates a Puppet Environment

    :param options: Check options using `hammer environment create --help` on satellite.

    :returns Environment object
    """
    # Assigning default values for attributes
    args = {
        'location-ids': None,
        'locations': None,
        'name': gen_alphanumeric(6),
        'organization-ids': None,
        'organizations': None,
    }

    return create_object(Environment, args, options)


@cacheable
def make_lifecycle_environment(options=None):
    """Creates a Lifecycle Environment

    :param options: Check options using `hammer lifecycle-environment create --help` on satellite.

    :returns LifecycleEnvironment object
    """
    # Organization Name, Label or ID is a required field.
    if (
        not options
        or 'organization' not in options
        and 'organization-label' not in options
        and 'organization-id' not in options
    ):
        raise CLIFactoryError('Please provide a valid Organization.')

    if not options.get('prior'):
        options['prior'] = 'Library'

    # Assigning default values for attributes
    args = {
        'description': None,
        'label': None,
        'name': gen_alphanumeric(6),
        'organization': None,
        'organization-id': None,
        'organization-label': None,
        'prior': None,
        'registry-name-pattern': None,
        'registry-unauthenticated-pull': None,
    }

    return create_object(LifecycleEnvironment, args, options)


@cacheable
def make_tailoringfile(options=None):
    """Creates a tailoring File

    :param options: Check options using `hammer tailoring-file create --help` on satellite.

    :returns TailoringFile object
    """
    # Assigning default values for attributes
    args = {
        'scap-file': None,
        'original-filename': None,
        'location-ids': None,
        'locations': None,
        'name': gen_alphanumeric().lower(),
        'organization-ids': None,
        'organizations': None,
    }

    return create_object(TailoringFiles, args, options)


@cacheable
def make_template(options=None):
    """Creates a Template

    :param options: Check options using `hammer template create --help` on satellite.

    :returns Template object
    """
    # Assigning default values for attribute
    args = {
        'audit-comment': None,
        'file': f'/root/{gen_alphanumeric()}',
        'location-ids': None,
        'locked': None,
        'name': gen_alphanumeric(6),
        'operatingsystem-ids': None,
        'organization-ids': None,
        'type': random.choice(constants.TEMPLATE_TYPES),
    }

    # Write content to file or random text
    if options is not None and 'content' in options.keys():
        content = options.pop('content')
    else:
        content = gen_alphanumeric()

    # Special handling for template factory
    (_, layout) = mkstemp(text=True)
    chmod(layout, 0o700)
    with open(layout, 'w') as ptable:
        ptable.write(content)
    # Upload file to server
    ssh.get_client().put(layout, args['file'])
    # End - Special handling for template factory

    return create_object(Template, args, options)


@cacheable
def make_template_input(options=None):
    """
    Creates Template Input

    :param options: Check options using `hammer template-input create --help` on satellite.

    :returns TemplateInput object
    """
    if not options or not options.get('input-type') or not options.get('template-id'):
        raise CLIFactoryError('Please provide valid template-id and input-type')

    args = {
        'advanced': None,
        'description': None,
        'fact-name': None,
        'input-type': None,
        'location': None,
        'location-id': None,
        'location-title': None,
        'name': gen_alphanumeric(6),
        'options': None,
        'organization': None,
        'organization-id': None,
        'organization-title': None,
        'puppet-class-name': None,
        'puppet-parameter-name': None,
        'required': None,
        'resource-type': None,
        'template-id': None,
        'value-type': None,
        'variable-name': None,
    }
    return create_object(TemplateInput, args, options)


@cacheable
def make_virt_who_config(options=None):
    """Creates a Virt Who Configuration

    :param options: Check options using `hammer virt-who-config create --help` on satellite.

    :returns VirtWhoConfig object
    """
    args = {
        'blacklist': None,
        'debug': None,
        'filtering-mode': 'none',
        'hypervisor-id': 'hostname',
        'hypervisor-password': None,
        'hypervisor-server': None,
        'hypervisor-type': None,
        'hypervisor-username': None,
        'interval': '60',
        'name': gen_alphanumeric(6),
        'no-proxy': None,
        'organization': None,
        'organization-id': None,
        'organization-title': None,
        'proxy': None,
        'satellite-url': settings.server.hostname,
        'whitelist': None,
    }
    return create_object(VirtWhoConfig, args, options)


def activationkey_add_subscription_to_repo(options=None):
    """Helper function that adds subscription to an activation key"""
    if (
        not options
        or not options.get('organization-id')
        or not options.get('activationkey-id')
        or not options.get('subscription')
    ):
        raise CLIFactoryError('Please provide valid organization, activation key and subscription.')
    # List the subscriptions in given org
    subscriptions = Subscription.list(
        {'organization-id': options['organization-id']}, per_page=False
    )
    # Add subscription to activation-key
    if options['subscription'] not in (sub['name'] for sub in subscriptions):
        raise CLIFactoryError(
            'Subscription {} not found in the given org'.format(options['subscription'])
        )
    for subscription in subscriptions:
        if subscription['name'] == options['subscription']:
            if subscription['quantity'] != 'Unlimited' and int(subscription['quantity']) == 0:
                raise CLIFactoryError('All the subscriptions are already consumed')
            try:
                ActivationKey.add_subscription(
                    {
                        'id': options['activationkey-id'],
                        'subscription-id': subscription['id'],
                        'quantity': 1,
                    }
                )
            except CLIReturnCodeError as err:
                raise CLIFactoryError(f'Failed to add subscription to activation key\n{err.msg}')


def setup_org_for_a_custom_repo(options=None):
    """Sets up Org for the given custom repo by:

    1. Checks if organization and lifecycle environment were given, otherwise
        creates new ones.
    2. Creates a new product with the custom repo. Synchronizes the repo.
    3. Checks if content view was given, otherwise creates a new one and
        - adds the RH repo
        - publishes
        - promotes to the lifecycle environment
    4. Checks if activation key was given, otherwise creates a new one and
        associates it with the content view.
    5. Adds the custom repo subscription to the activation key

    :return: A dictionary with the entity ids of Activation key, Content view,
        Lifecycle Environment, Organization, Product and Repository

    """
    if not options or not options.get('url'):
        raise CLIFactoryError('Please provide valid custom repo URL.')
    # Create new organization and lifecycle environment if needed
    if options.get('organization-id') is None:
        org_id = make_org()['id']
    else:
        org_id = options['organization-id']
    if options.get('lifecycle-environment-id') is None:
        env_id = make_lifecycle_environment({'organization-id': org_id})['id']
    else:
        env_id = options['lifecycle-environment-id']
    # Create custom product and repository
    custom_product = make_product({'organization-id': org_id})
    custom_repo = make_repository(
        {'content-type': 'yum', 'product-id': custom_product['id'], 'url': options.get('url')}
    )
    # Synchronize custom repository
    try:
        Repository.synchronize({'id': custom_repo['id']})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to synchronize repository\n{err.msg}')
    # Create CV if needed and associate repo with it
    if options.get('content-view-id') is None:
        cv_id = make_content_view({'organization-id': org_id})['id']
    else:
        cv_id = options['content-view-id']
    try:
        ContentView.add_repository(
            {'id': cv_id, 'organization-id': org_id, 'repository-id': custom_repo['id']}
        )
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to add repository to content view\n{err.msg}')
    # Publish a new version of CV
    try:
        ContentView.publish({'id': cv_id})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to publish new version of content view\n{err.msg}')
    # Get the version id
    cvv = ContentView.info({'id': cv_id})['versions'][-1]
    # Promote version to next env
    try:
        ContentView.version_promote(
            {'id': cvv['id'], 'organization-id': org_id, 'to-lifecycle-environment-id': env_id}
        )
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to promote version to next environment\n{err.msg}')
    # Create activation key if needed and associate content view with it
    if options.get('activationkey-id') is None:
        activationkey_id = make_activation_key(
            {
                'content-view-id': cv_id,
                'lifecycle-environment-id': env_id,
                'organization-id': org_id,
            }
        )['id']
    else:
        activationkey_id = options['activationkey-id']
        # Given activation key may have no (or different) CV associated.
        # Associate activation key with CV just to be sure
        try:
            ActivationKey.update(
                {'content-view-id': cv_id, 'id': activationkey_id, 'organization-id': org_id}
            )
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to associate activation-key with CV\n{err.msg}')
    # Add subscription to activation-key
    activationkey_add_subscription_to_repo(
        {
            'activationkey-id': activationkey_id,
            'organization-id': org_id,
            'subscription': custom_product['name'],
        }
    )
    return {
        'activationkey-id': activationkey_id,
        'content-view-id': cv_id,
        'lifecycle-environment-id': env_id,
        'organization-id': org_id,
        'product-id': custom_product['id'],
        'repository-id': custom_repo['id'],
    }


def _setup_org_for_a_rh_repo(options=None):
    """Sets up Org for the given Red Hat repository by:

    1. Checks if organization and lifecycle environment were given, otherwise
        creates new ones.
    2. Clones and uploads manifest.
    3. Enables RH repo and synchronizes it.
    4. Checks if content view was given, otherwise creates a new one and
        - adds the RH repo
        - publishes
        - promotes to the lifecycle environment
    5. Checks if activation key was given, otherwise creates a new one and
        associates it with the content view.
    6. Adds the RH repo subscription to the activation key

    Note that in most cases you should use ``setup_org_for_a_rh_repo`` instead
    as it's more flexible.

    :return: A dictionary with the entity ids of Activation key, Content view,
        Lifecycle Environment, Organization and Repository

    """
    if (
        not options
        or not options.get('product')
        or not options.get('repository-set')
        or not options.get('repository')
    ):
        raise CLIFactoryError('Please provide valid product, repository-set and repo.')
    # Create new organization and lifecycle environment if needed
    if options.get('organization-id') is None:
        org_id = make_org()['id']
    else:
        org_id = options['organization-id']
    if options.get('lifecycle-environment-id') is None:
        env_id = make_lifecycle_environment({'organization-id': org_id})['id']
    else:
        env_id = options['lifecycle-environment-id']
    # Clone manifest and upload it
    with manifests.clone() as manifest:
        ssh.get_client().put(manifest, manifest.filename)
    try:
        Subscription.upload({'file': manifest.filename, 'organization-id': org_id})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to upload manifest\n{err.msg}')
    # Enable repo from Repository Set
    try:
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': options['repository-set'],
                'organization-id': org_id,
                'product': options['product'],
                'releasever': options.get('releasever'),
            }
        )
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to enable repository set\n{err.msg}')
    # Fetch repository info
    try:
        rhel_repo = Repository.info(
            {
                'name': options['repository'],
                'organization-id': org_id,
                'product': options['product'],
            }
        )
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to fetch repository info\n{err.msg}')
    # Synchronize the RH repository
    try:
        Repository.synchronize(
            {
                'name': options['repository'],
                'organization-id': org_id,
                'product': options['product'],
            }
        )
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to synchronize repository\n{err.msg}')
    # Create CV if needed and associate repo with it
    if options.get('content-view-id') is None:
        cv_id = make_content_view({'organization-id': org_id})['id']
    else:
        cv_id = options['content-view-id']
    try:
        ContentView.add_repository(
            {'id': cv_id, 'organization-id': org_id, 'repository-id': rhel_repo['id']}
        )
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to add repository to content view\n{err.msg}')
    # Publish a new version of CV
    try:
        ContentView.publish({'id': cv_id})
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to publish new version of content view\n{err.msg}')
    # Get the version id
    try:
        cvv = ContentView.info({'id': cv_id})['versions'][-1]
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to fetch content view info\n{err.msg}')
    # Promote version1 to next env
    try:
        ContentView.version_promote(
            {'id': cvv['id'], 'organization-id': org_id, 'to-lifecycle-environment-id': env_id}
        )
    except CLIReturnCodeError as err:
        raise CLIFactoryError(f'Failed to promote version to next environment\n{err.msg}')
    # Create activation key if needed and associate content view with it
    if options.get('activationkey-id') is None:
        activationkey_id = make_activation_key(
            {
                'content-view-id': cv_id,
                'lifecycle-environment-id': env_id,
                'organization-id': org_id,
            }
        )['id']
    else:
        activationkey_id = options['activationkey-id']
        # Given activation key may have no (or different) CV associated.
        # Associate activation key with CV just to be sure
        try:
            ActivationKey.update(
                {'id': activationkey_id, 'organization-id': org_id, 'content-view-id': cv_id}
            )
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to associate activation-key with CV\n{err.msg}')
    # Add subscription to activation-key
    activationkey_add_subscription_to_repo(
        {
            'organization-id': org_id,
            'activationkey-id': activationkey_id,
            'subscription': options.get('subscription', constants.DEFAULT_SUBSCRIPTION_NAME),
        }
    )
    return {
        'activationkey-id': activationkey_id,
        'content-view-id': cv_id,
        'lifecycle-environment-id': env_id,
        'organization-id': org_id,
        'repository-id': rhel_repo['id'],
    }


def setup_org_for_a_rh_repo(options=None, force_manifest_upload=False, force_use_cdn=False):
    """Wrapper above ``_setup_org_for_a_rh_repo`` to use custom downstream repo
    instead of CDN's 'Satellite Capsule', 'Satellite Tools'  and base OS repos if
    ``settings.robottelo.cdn == 0`` and URL for custom repositories is set in properties.

    :param options: a dict with options to pass to function
        ``_setup_org_for_a_rh_repo``. See its docstring for more details
    :param force_use_cdn: bool flag whether to use CDN even if there's
        downstream repo available and ``settings.robottelo.cdn == 0``.
    :param force_manifest_upload: bool flag whether to upload a manifest to
        organization even if downstream custom repo is used instead of CDN.
        Useful when test relies on organization with manifest (e.g. uses some
        other RH repo afterwards). Defaults to False.
    :return: a dict with entity ids (see ``_setup_org_for_a_rh_repo`` and
        ``setup_org_for_a_custom_repo``).
    """
    custom_repo_url = None
    if options.get('repository') == constants.REPOS['rhst6']['name']:
        custom_repo_url = settings.repos.sattools_repo.rhel6
    elif options.get('repository') == constants.REPOS['rhst7']['name']:
        custom_repo_url = settings.repos.sattools_repo.rhel7
    elif options.get('repository') == constants.REPOS['rhel6']['name']:
        custom_repo_url = settings.repos.rhel6_os
    elif options.get('repository') == constants.REPOS['rhel7']['name']:
        custom_repo_url = settings.repos.rhel7_os
    elif 'Satellite Capsule' in options.get('repository'):
        custom_repo_url = settings.repos.capsule_repo
    if force_use_cdn or settings.robottelo.cdn or not custom_repo_url:
        return _setup_org_for_a_rh_repo(options)
    else:
        options['url'] = custom_repo_url
        result = setup_org_for_a_custom_repo(options)
        if force_manifest_upload:
            with manifests.clone() as manifest:
                ssh.get_client().put(manifest, manifest.filename)
            try:
                Subscription.upload(
                    {'file': manifest.filename, 'organization-id': result.get('organization-id')}
                )
            except CLIReturnCodeError as err:
                raise CLIFactoryError(f'Failed to upload manifest\n{err.msg}')
            # attach the default subscription to activation key
            activationkey_add_subscription_to_repo(
                {
                    'activationkey-id': result['activationkey-id'],
                    'organization-id': result['organization-id'],
                    'subscription': constants.DEFAULT_SUBSCRIPTION_NAME,
                }
            )
        return result


def configure_env_for_provision(org=None, loc=None):
    """Create and configure org, loc, product, repo, env. Update proxy,
    domain, subnet, compute resource, provision templates and medium with
    previously created entities and create a hostgroup using all mentioned
    entities.

    :param org: Default Organization that should be used in both host
        discovering and host provisioning procedures
    :param loc: Default Location that should be used in both host
        discovering and host provisioning procedures
    :return: List of created entities that can be re-used further in
        provisioning or validation procedure (e.g. hostgroup or subnet)
    """
    # Create new organization and location in case they were not passed
    if org is None:
        org = make_org()
    if loc is None:
        loc = make_location()

    # Get a Library Lifecycle environment and the default CV for the org
    lce = LifecycleEnvironment.info({'name': 'Library', 'organization-id': org['id']})
    cv = ContentView.info({'name': 'Default Organization View', 'organization-id': org['id']})

    # Create puppet environment and associate organization and location
    env = make_environment({'location-ids': loc['id'], 'organization-ids': org['id']})

    # get default capsule and associate location
    puppet_proxy = Proxy.info({'id': Proxy.list({'search': settings.server.hostname})[0]['id']})
    Proxy.update(
        {
            'id': puppet_proxy['id'],
            'locations': list(set(puppet_proxy.get('locations') or []) | {loc['name']}),
        }
    )

    # Network
    # Search for existing domain or create new otherwise. Associate org,
    # location and dns to it
    _, _, domain_name = settings.server.hostname.partition('.')
    domain = Domain.list({'search': f'name={domain_name}'})
    if len(domain) == 1:
        domain = Domain.info({'id': domain[0]['id']})
        Domain.update(
            {
                'name': domain_name,
                'locations': list(set(domain.get('locations') or []) | {loc['name']}),
                'organizations': list(set(domain.get('organizations') or []) | {org['name']}),
                'dns-id': puppet_proxy['id'],
            }
        )
    else:
        # Create new domain
        domain = make_domain(
            {
                'name': domain_name,
                'location-ids': loc['id'],
                'organization-ids': org['id'],
                'dns-id': puppet_proxy['id'],
            }
        )
    # Search if subnet is defined with given network. If so, just update its
    # relevant fields otherwise create new subnet
    network = settings.vlan_networking.subnet
    subnet = Subnet.list({'search': f'network={network}'})
    if len(subnet) >= 1:
        subnet = Subnet.info({'id': subnet[0]['id']})
        Subnet.update(
            {
                'name': subnet['name'],
                'domains': list(set(subnet.get('domains') or []) | {domain['name']}),
                'locations': list(set(subnet.get('locations') or []) | {loc['name']}),
                'organizations': list(set(subnet.get('organizations') or []) | {org['name']}),
                'dhcp-id': puppet_proxy['id'],
                'dns-id': puppet_proxy['id'],
                'tftp-id': puppet_proxy['id'],
            }
        )
    else:
        # Create new subnet
        subnet = make_subnet(
            {
                'name': gen_string('alpha'),
                'network': network,
                'mask': settings.vlan_networking.netmask,
                'domain-ids': domain['id'],
                'location-ids': loc['id'],
                'organization-ids': org['id'],
                'dhcp-id': puppet_proxy['id'],
                'dns-id': puppet_proxy['id'],
                'tftp-id': puppet_proxy['id'],
            }
        )

    # Get the Partition table entity
    ptable = PartitionTable.info({'name': constants.DEFAULT_PTABLE})

    # Get the OS entity
    os = OperatingSys.list({'search': 'name="RedHat" AND (major="6" OR major="7")'})[0]

    # Get proper Provisioning templates and update with OS, Org, Location
    provisioning_template = Template.info({'name': constants.DEFAULT_TEMPLATE})
    pxe_template = Template.info({'name': constants.DEFAULT_PXE_TEMPLATE})
    for template in provisioning_template, pxe_template:
        if os['title'] not in template['operating-systems']:
            Template.update(
                {
                    'id': template['id'],
                    'locations': list(set(template.get('locations') or []) | {loc['name']}),
                    'operatingsystems': list(
                        set(template.get('operating-systems') or []) | {os['title']}
                    ),
                    'organizations': list(set(template.get('organizations') or []) | {org['name']}),
                }
            )

    # Get the architecture entity
    arch = Architecture.list({'search': f'name={constants.DEFAULT_ARCHITECTURE}'})[0]

    os = OperatingSys.info({'id': os['id']})
    # Get the media and update its location
    medium = Medium.list({'search': f'path={settings.repos.rhel7_os}'})
    if medium:
        media = Medium.info({'id': medium[0]['id']})
        Medium.update(
            {
                'id': media['id'],
                'operatingsystems': list(set(media.get('operating-systems') or []) | {os['title']}),
                'locations': list(set(media.get('locations') or []) | {loc['name']}),
                'organizations': list(set(media.get('organizations') or []) | {org['name']}),
            }
        )
    else:
        media = make_medium(
            {
                'location-ids': loc['id'],
                'operatingsystem-ids': os['id'],
                'organization-ids': org['id'],
                'path': settings.repos.rhel7_os,
            }
        )

    # Update the OS with found arch, ptable, templates and media
    OperatingSys.update(
        {
            'id': os['id'],
            'architectures': list(set(os.get('architectures') or []) | {arch['name']}),
            'media': list(set(os.get('installation-media') or []) | {media['name']}),
            'partition-tables': list(set(os.get('partition-tables') or []) | {ptable['name']}),
        }
    )
    for template in (provisioning_template, pxe_template):
        if '{} ({})'.format(template['name'], template['type']) not in os['templates']:
            OperatingSys.update(
                {
                    'id': os['id'],
                    'provisioning-templates': list(set(os['templates']) | {template['name']}),
                }
            )

    # Create new hostgroup using proper entities
    hostgroup = make_hostgroup(
        {
            'location-ids': loc['id'],
            'environment-id': env['id'],
            'lifecycle-environment-id': lce['id'],
            'puppet-proxy-id': puppet_proxy['id'],
            'puppet-ca-proxy-id': puppet_proxy['id'],
            'content-view-id': cv['id'],
            'domain-id': domain['id'],
            'subnet-id': subnet['id'],
            'organization-ids': org['id'],
            'architecture-id': arch['id'],
            'partition-table-id': ptable['id'],
            'medium-id': media['id'],
            'operatingsystem-id': os['id'],
            'root-password': gen_string('alphanumeric'),
            'content-source-id': puppet_proxy['id'],
        }
    )

    return {'hostgroup': hostgroup, 'subnet': subnet, 'domain': domain, 'ptable': ptable, 'os': os}


def _get_capsule_vm_distro_repos(distro):
    """Return the right RH repos info for the capsule setup"""
    rh_repos = []
    if distro == 'rhel7':
        # Red Hat Enterprise Linux 7 Server
        rh_product_arch = constants.REPOS['rhel7']['arch']
        rh_product_releasever = constants.REPOS['rhel7']['releasever']
        rh_repos.append(
            {
                'product': constants.PRDS['rhel'],
                'repository-set': constants.REPOSET['rhel7'],
                'repository': constants.REPOS['rhel7']['name'],
                'repository-id': constants.REPOS['rhel7']['id'],
                'releasever': rh_product_releasever,
                'arch': rh_product_arch,
                'cdn': True,
            }
        )
        # Red Hat Software Collections (for 7 Server)
        rh_repos.append(
            {
                'product': constants.PRDS['rhscl'],
                'repository-set': constants.REPOSET['rhscl7'],
                'repository': constants.REPOS['rhscl7']['name'],
                'repository-id': constants.REPOS['rhscl7']['id'],
                'releasever': rh_product_releasever,
                'arch': rh_product_arch,
                'cdn': True,
            }
        )
        # Red Hat Satellite Capsule 6.2 (for RHEL 7 Server)
        rh_repos.append(
            {
                'product': constants.PRDS['rhsc'],
                'repository-set': constants.REPOSET['rhsc7'],
                'repository': constants.REPOS['rhsc7']['name'],
                'repository-id': constants.REPOS['rhsc7']['id'],
                'url': settings.repos.capsule_repo,
                'cdn': settings.robottelo.cdn or not settings.repos.capsule_repo,
            }
        )
    else:
        raise CLIFactoryError(f'distro "{distro}" not supported')

    return rh_product_arch, rh_product_releasever, rh_repos


def add_role_permissions(role_id, resource_permissions):
    """Create role permissions found in resource permissions dict

    :param role_id: The role id
    :param resource_permissions: a dict containing resources with permission
        names and other Filter options

    Usage::

        role = make_role({'organization-id': org['id']})
        resource_permissions = {
            'Katello::ActivationKey': {
                'permissions': [
                    'view_activation_keys',
                    'create_activation_keys',
                    'edit_activation_keys',
                    'destroy_activation_keys'
                ],
                'search': "name ~ {}".format(ak_name_like)
            },
        }
        add_role_permissions(role['id'], resource_permissions)
    """
    available_permissions = Filter.available_permissions()
    # group the available permissions by resource type
    available_rc_permissions = {}
    for permission in available_permissions:
        permission_resource = permission['resource']
        if permission_resource not in available_rc_permissions:
            available_rc_permissions[permission_resource] = []
        available_rc_permissions[permission_resource].append(permission)
    # create only the required role permissions per resource type
    for resource_type, permission_data in resource_permissions.items():
        permission_names = permission_data.get('permissions')
        if permission_names is None:
            raise CLIFactoryError(f'Permissions not provided for resource: {resource_type}')
        # ensure  that the required resource type is available
        if resource_type not in available_rc_permissions:
            raise CLIFactoryError(
                f'Resource "{resource_type}" not in the list of available resources'
            )
        available_permission_names = [
            permission['name']
            for permission in available_rc_permissions[resource_type]
            if permission['name'] in permission_names
        ]
        # ensure that all the required permissions are available
        missing_permissions = set(permission_names).difference(set(available_permission_names))
        if missing_permissions:
            raise CLIFactoryError(
                'Permissions "{}" are not available in Resource "{}"'.format(
                    list(missing_permissions), resource_type
                )
            )
        # Create the current resource type role permissions
        options = {'role-id': role_id}
        options.update(permission_data)
        make_filter(options=options)


def setup_cdn_and_custom_repositories(org_id, repos, download_policy='on_demand', synchronize=True):
    """Setup cdn and custom repositories

    :param int org_id: The organization id
    :param list repos: a list of dict repositories options
    :param str download_policy: update the repositories with this download
        policy
    :param bool synchronize: Whether to synchronize the repositories.
    :return: a dict containing the content view and repos info
    """
    custom_product = None
    repos_info = []
    for repo in repos:
        custom_repo_url = repo.get('url')
        cdn = repo.get('cdn', False)
        if not cdn and not custom_repo_url:
            raise CLIFactoryError('Custom repository with url not supplied')
        if cdn:
            RepositorySet.enable(
                {
                    'organization-id': org_id,
                    'product': repo['product'],
                    'name': repo['repository-set'],
                    'basearch': repo.get('arch', constants.DEFAULT_ARCHITECTURE),
                    'releasever': repo.get('releasever'),
                }
            )
            repo_info = Repository.info(
                {'organization-id': org_id, 'name': repo['repository'], 'product': repo['product']}
            )
        else:
            if custom_product is None:
                custom_product = make_product_wait({'organization-id': org_id})
            repo_info = make_repository(
                {
                    'product-id': custom_product['id'],
                    'organization-id': org_id,
                    'url': custom_repo_url,
                }
            )
        if download_policy:
            # Set download policy
            Repository.update({'download-policy': download_policy, 'id': repo_info['id']})
        repos_info.append(repo_info)
    if synchronize:
        # Synchronize the repositories
        for repo_info in repos_info:
            Repository.synchronize({'id': repo_info['id']}, timeout=4800000)
    return custom_product, repos_info


def setup_cdn_and_custom_repos_content(
    org_id,
    lce_id=None,
    repos=None,
    upload_manifest=True,
    download_policy='on_demand',
    rh_subscriptions=None,
    default_cv=False,
):
    """Setup cdn and custom repositories, content view and activations key

    :param int org_id: The organization id
    :param int lce_id: the lifecycle environment id
    :param list repos: a list of dict repositories options
    :param bool default_cv: whether to use the Default Organization CV
    :param bool upload_manifest: whether to upload the organization manifest
    :param str download_policy: update the repositories with this download
        policy
    :param list rh_subscriptions: a list of RH subscription to attach to
        activation key
    :return: a dict containing the activation key, content view and repos info
    """
    if lce_id is None and not default_cv:
        raise TypeError('lce_id must be specified')
    if repos is None:
        repos = []
    if rh_subscriptions is None:
        rh_subscriptions = []

    if upload_manifest:
        # Upload the organization manifest
        try:
            manifests.upload_manifest_locked(org_id, manifests.clone(), interface='CLI')
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to upload manifest\n{err.msg}')

    custom_product, repos_info = setup_cdn_and_custom_repositories(
        org_id=org_id, repos=repos, download_policy=download_policy
    )
    if default_cv:
        activation_key = make_activation_key(
            {'organization-id': org_id, 'lifecycle-environment': 'Library'}
        )
        content_view = ContentView.info(
            {'organization-id': org_id, 'name': 'Default Organization View'}
        )
    else:
        # Create a content view
        content_view = make_content_view({'organization-id': org_id})
        # Add repositories to content view
        for repo_info in repos_info:
            ContentView.add_repository(
                {
                    'id': content_view['id'],
                    'organization-id': org_id,
                    'repository-id': repo_info['id'],
                }
            )
        # Publish the content view
        ContentView.publish({'id': content_view['id']})
        # Get the latest content view version id
        content_view_version = ContentView.info({'id': content_view['id']})['versions'][-1]
        # Promote content view version to lifecycle environment
        ContentView.version_promote(
            {
                'id': content_view_version['id'],
                'organization-id': org_id,
                'to-lifecycle-environment-id': lce_id,
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        activation_key = make_activation_key(
            {
                'organization-id': org_id,
                'lifecycle-environment-id': lce_id,
                'content-view-id': content_view['id'],
            }
        )
    # Get organization subscriptions
    subscriptions = Subscription.list({'organization-id': org_id}, per_page=False)
    # Add subscriptions to activation-key
    needed_subscription_names = list(rh_subscriptions)
    if custom_product:
        needed_subscription_names.append(custom_product['name'])
    added_subscription_names = []
    for subscription in subscriptions:
        if (
            subscription['name'] in needed_subscription_names
            and subscription['name'] not in added_subscription_names
        ):
            ActivationKey.add_subscription(
                {'id': activation_key['id'], 'subscription-id': subscription['id'], 'quantity': 1}
            )
            added_subscription_names.append(subscription['name'])
            if len(added_subscription_names) == len(needed_subscription_names):
                break
    missing_subscription_names = set(needed_subscription_names).difference(
        set(added_subscription_names)
    )
    if missing_subscription_names:
        raise CLIFactoryError(f'Missing subscriptions: {missing_subscription_names}')
    data = dict(
        activation_key=activation_key,
        content_view=content_view,
        product=custom_product,
        repos=repos_info,
    )
    if lce_id:
        lce = LifecycleEnvironment.info({'id': lce_id, 'organization-id': org_id})
        data['lce'] = lce

    return data


@cacheable
def make_http_proxy(options=None):
    """Creates a HTTP Proxy

    :param options: Check options using `hammer http-proxy create --help` on satellite.

    :returns HttpProxy object
    """
    # Assigning default values for attributes
    args = {
        'location': None,
        'location-id': None,
        'location-title': None,
        'locations': None,
        'location-ids': None,
        'location-titles': None,
        'name': gen_string('alpha', 15),
        'organization': None,
        'organization-id': None,
        'organization-title': None,
        'organizations': None,
        'organization-ids': None,
        'organization-titles': None,
        'password': None,
        'url': '{}:{}'.format(gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999)),
        'username': None,
    }

    return create_object(HttpProxy, args, options)
