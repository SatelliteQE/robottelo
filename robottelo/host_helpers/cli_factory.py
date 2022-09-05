"""
This module is a more object oriented replacement for robottelo.cli.factory
It is not meant to be used directly, but as part of a robottelo.hosts.Satellite instance
example: my_satellite.cli_factory.make_org()
"""
import datetime
import inspect
import os
import pprint
import random
from functools import lru_cache
from functools import partial
from os import chmod
from tempfile import mkstemp
from time import sleep

from box import Box
from fauxfactory import gen_alpha
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_choice
from fauxfactory import gen_integer
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_netmask
from fauxfactory import gen_url

from robottelo import constants
from robottelo import manifests
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.config import settings
from robottelo.host_helpers.repository_mixins import initiate_repo_helpers


class CLIFactoryError(Exception):
    """Indicates an error occurred while creating an entity using hammer"""


def create_object(cli_object, options, values=None, credentials=None):
    """
    Creates <object> with dictionary of arguments.

    :param cli_object: A valid CLI object.
    :param dict options: The default options accepted by the cli_object
        create
    :param dict values: Custom values to override default ones.
    :param list|tuple credentials: Username and password for non-default user.
    :raise robottelo.host_helpers.cli_factory.CLIFactoryError: Raise an exception if object
        cannot be created.
    :rtype: dict
    :return: A dictionary representing the newly created resource.

    """
    options.update(values or {})
    if credentials:
        cli_object = cli_object.with_user(*credentials)
    try:
        result = cli_object.create(options)
    except CLIReturnCodeError as err:
        # If the object is not created, raise exception, stop the show.
        raise CLIFactoryError(
            'Failed to create {} with data:\n{}\n{}'.format(
                cli_object.__name__, pprint.pformat(options, indent=2), err.msg
            )
        )
    # Sometimes we get a list with a dictionary and not a dictionary.
    if type(result) is list and len(result) > 0:
        result = result[0]
    return Box(result)


"""
The following dictionary is used to define the simple make methods in this factory.
Each key corresponds to the name of the entity (e.g. make_<entity_name>)
The value of each entity key is a dictionary containing the following:
    <option_name>: <value population function> Functions will be evaluated at runtime
    _setup: <setup function>  Use this when a little more complexity is needed (see below)
    _setup_args: [list of arguments for setup function]
    _setup_kwargs: {dict of keyword arguments for setup function}
    _redirect: 'name of make_<entity> function that should actually be ran'
    _entity_cls: 'name of the EntityClass that should be used instead of key name'
"""
ENTITY_FIELDS = {
    'activation_key': {
        'name': gen_alphanumeric,
    },
    'architecture': {
        'name': gen_alphanumeric,
    },
    'content_view': {'_redirect': 'content_view_with_credentials'},
    'content_view_with_credentials': {
        '_entity_cls': 'ContentView',
        'name': gen_alpha,
    },
    'content_view_filter': {
        'name': gen_alpha,
    },
    'content_view_filter_rule': {},
    'discoveryrule': {
        'name': gen_alphanumeric,
    },
    'http_proxy': {
        'name': gen_alpha,
        'url': lambda: '{}:{}'.format(
            gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999)
        ),
    },
    'location': {
        'name': gen_alphanumeric,
    },
    'model': {
        'name': gen_alphanumeric,
    },
    'partition_table': {
        'file': lambda: f'/tmp/{gen_alphanumeric()}',
        'name': gen_alphanumeric,
        'os-family': partial(gen_choice, constants.OPERATING_SYSTEMS),
    },
    'product': {'_redirect': 'product_with_credentials'},
    'product_with_credentials': {
        '_entity_cls': 'Product',
        'description': gen_alpha,
        'label': gen_alpha,
        'name': gen_alpha,
    },
    'repository': {'_redirect': 'repository_with_credentials'},
    'repository_with_credentials': {
        '_entity_cls': 'Repository',
        'name': gen_alpha,
        'url': settings.repos.yum_1.url,
    },
    'role': {'name': gen_alphanumeric},
    'filter': {},
    'scap_policy': {
        'name': lambda: gen_alphanumeric().lower(),
    },
    'subnet': {
        'mask': gen_netmask,
        'name': gen_alphanumeric,
        'network': partial(gen_ipaddr, True),
    },
    'sync_plan': {
        'description': gen_alpha,
        'enabled': 'true',
        'interval': lambda: random.choice(list(constants.SYNC_INTERVAL.values())),
        'name': gen_alpha,
        'sync-date': lambda: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    },
    'host': {
        'ip': gen_ipaddr,
        'mac': partial(gen_mac, multicast=False),
        'name': gen_alpha,
        'root-password': gen_alpha,
    },
    'host_collection': {
        'name': gen_alpha,
    },
    'job_invocation': {},
    'job_template': {
        'job-category': 'Miscellaneous',
        'provider-type': 'SSH',
    },
    'user': {
        '_setup': gen_alphanumeric,  # create a login name
        'auth-source-id': 1,
        'firstname': gen_alphanumeric,
        'lastname': gen_alphanumeric,
        'login': lambda: ENTITY_FIELDS['user']['_setup_res'],
        'mail': lambda: f"{ENTITY_FIELDS['user']['_setup_res']}@example.com",
        'password': gen_alphanumeric,
    },
    'usergroup': {
        'name': gen_alphanumeric,
    },
    'usergroup_external': {
        'auth-source-id': 1,
        'name': gen_alphanumeric,
    },
    'ldap_auth_source': {
        'name': gen_alphanumeric,
    },
    'compute_resource': {
        'name': gen_alphanumeric,
    },
    'org': {'_redirect': 'org_with_credentials'},
    'org_with_credentials': {
        '_entity_cls': 'Org',
        'name': gen_alphanumeric,
    },
    'realm': {
        'name': gen_alphanumeric,
    },
    'report_template': {
        'file': gen_alphanumeric,  # formerly content
        'name': gen_alphanumeric,
    },
    'os': {
        'major': partial(random.randint, 0, 10),
        'minor': partial(random.randint, 0, 10),
        'name': gen_alphanumeric,
    },
    'scapcontent': {
        '_entity_cls': 'Scapcontent',
        'title': gen_alphanumeric().lower(),
    },
    'domain': {
        '_entity_cls': 'Domain',
        'name': lambda: gen_alphanumeric().lower(),
    },
    'hostgroup': {
        '_entity_cls': 'HostGroup',
        'name': gen_alphanumeric,
    },
    'medium': {
        '_entity_cls': 'Medium',
        'name': gen_alphanumeric,
        'path': lambda: f'http://{gen_alpha()}',
    },
    'environment': {
        '_entity_cls': 'Environment',
        'name': gen_alphanumeric,
    },
    'lifecycle_environment': {
        '_entity_cls': 'LifecycleEnvironment',
        'prior': 'Library',
        'name': gen_alphanumeric,
    },
    'tailoringfile': {
        '_entity_cls': 'TailoringFiles',
        'name': lambda: gen_alphanumeric().lower(),
    },
    'template_input': {
        '_entity_cls': 'TemplateInput',
        'name': gen_alphanumeric,
    },
    'virt_who_config': {
        'filtering-mode': 'none',
        'hypervisor-id': 'hostname',
        'interval': '60',
        'name': gen_alphanumeric,
        'satellite-url': lambda self: self._satellite.hostname,
    },
}


class CLIFactory:
    """This class is part of a mixin and not to be used directly. See robottelo.hosts.Satellite"""

    def __init__(self, satellite):
        self._satellite = satellite
        self.__dict__.update(initiate_repo_helpers(self._satellite))

    def __getattr__(self, name):
        """We intercept the usual attribute behavior on this class to emulate make_entity methods
        The keys in the dictionary above correspond to potential make_<key> methods
        These are all basic cases where the make method just need some default values.
        For more complex make methods, we define them in methods below.
        """
        fields = ENTITY_FIELDS.get(name.replace('make_', ''))
        if isinstance(fields, dict):
            # someone is attempting to use a make_<entity> method
            if setup := fields.get('_setup'):
                # check for an evaluate _setup fields
                fields['_setup_res'] = setup(
                    *fields.get('_setup_args', []), **fields.get('_setup_kwargs', {})
                )
            # sometimes entity class names don't match the make_<entity> pattern
            entity_cls = self._find_entity_class(
                fields.get('_entity_cls', name.replace('make_', ''))
            )
            # some make_<entity> calls redirect to other methods
            if redirect := fields.get('_redirect'):
                return self.__getattr__(redirect)
            # evaluate functions that provide default values
            fields = self._evaluate_functions(fields)
            return partial(create_object, entity_cls, fields)
        else:
            raise AttributeError(f'unknown factory method name: {name}')

    def _evaluate_function(self, function):
        """Some functions may require an instance reference"""
        if 'self' in inspect.signature(function).parameters:
            return function(self)
        else:
            return function()

    def _evaluate_functions(self, iterable):
        """Run functions that are used to populate data in lists/dicts"""
        if isinstance(iterable, list):
            return [self._evaluate_function(item) if callable(item) else item for item in iterable]
        if isinstance(iterable, dict):
            return {
                key: (self._evaluate_function(item) if callable(item) else item)
                for key, item in iterable.items()
                if not key.startswith('_')
            }

    @lru_cache
    def _find_entity_class(self, entity_name):
        entity_name = entity_name.replace('_', '').lower()
        for name, class_obj in self._satellite.cli.__dict__.items():
            if entity_name == name.lower():
                return class_obj

    def make_content_credential(self, options=None):
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
        self._satellite.put(key_filename, args['path'])

        return create_object(self._satellite.cli.ContentCredential, args, options)

    def make_partition_table(self, options=None):
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
        self._satellite.put(layout, args['file'])

        return create_object(self._satellite.cli.PartitionTable, args, options)

    def make_product_wait(self, options=None, wait_for=5):
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
        options['name'] = options.get('name', gen_alpha())
        try:
            product = self.make_product(options)
        except CLIFactoryError as err:
            sleep(wait_for)
            try:
                product = self._satellite.cli.Product.info(
                    {'name': options.get('name'), 'organization-id': options.get('organization-id')}
                )
            except CLIReturnCodeError:
                raise err
            if not product:
                raise err
        return product

    def make_fake_host(self, options=None):
        """Wrapper function for make_host to pass all required options for creation
        of a fake host
        """
        if options is None:
            options = {}

        # Try to use default Satellite entities, otherwise create them if they were
        # not passed or defined previously
        if not options.get('organization') and not options.get('organization-id'):
            try:
                options['organization-id'] = self._satellite.cli.Org.info(
                    {'name': constants.DEFAULT_ORG}
                )['id']
            except CLIReturnCodeError:
                options['organization-id'] = self.make_org()['id']
        if not options.get('location') and not options.get('location-id'):
            try:
                options['location-id'] = self._satellite.cli.Location.info(
                    {'name': constants.DEFAULT_LOC}
                )['id']
            except CLIReturnCodeError:
                options['location-id'] = self.make_location()['id']
        if not options.get('domain') and not options.get('domain-id'):
            options['domain-id'] = self.make_domain(
                {
                    'location-ids': options.get('location-id'),
                    'locations': options.get('location'),
                    'organization-ids': options.get('organization-id'),
                    'organizations': options.get('organization'),
                }
            )['id']
        if not options.get('architecture') and not options.get('architecture-id'):
            try:
                options['architecture-id'] = self._satellite.cli.Architecture.info(
                    {'name': constants.DEFAULT_ARCHITECTURE}
                )['id']
            except CLIReturnCodeError:
                options['architecture-id'] = self.make_architecture()['id']
        if not options.get('operatingsystem') and not options.get('operatingsystem-id'):
            try:
                options['operatingsystem-id'] = self._satellite.cli.OperatingSys.list(
                    {'search': 'name="RedHat" AND (major="7" OR major="8")'}
                )[0]['id']
            except IndexError:
                options['operatingsystem-id'] = self.make_os(
                    {
                        'architecture-ids': options.get('architecture-id'),
                        'architectures': options.get('architecture'),
                        'partition-table-ids': options.get('partition-table-id'),
                        'partition-tables': options.get('partition-table'),
                    }
                )['id']
        if not options.get('partition-table') and not options.get('partition-table-id'):
            try:
                options['partition-table-id'] = self._satellite.cli.PartitionTable.list(
                    {
                        'operatingsystem': options.get('operatingsystem'),
                        'operatingsystem-id': options.get('operatingsystem-id'),
                    }
                )[0]['id']
            except IndexError:
                options['partition-table-id'] = self.make_partition_table(
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
            options['medium-id'] = self.make_medium(
                {
                    'location-ids': options.get('location-id'),
                    'locations': options.get('location'),
                    'operatingsystems': options.get('operatingsystem'),
                    'operatingsystem-ids': options.get('operatingsystem-id'),
                    'organization-ids': options.get('organization-id'),
                    'organizations': options.get('organization'),
                }
            )['id']

        return self.make_host(options)

    def make_proxy(self, options=None):
        """Creates a Proxy

        :param options: Check options using `hammer proxy create --help` on satellite.

        :returns Proxy object
        """
        args = {'name': gen_alphanumeric()}

        if options is None or 'url' not in options:
            newport = self._satellite.available_capsule_port
            try:
                with self._satellite.default_url_on_new_port(9090, newport) as url:
                    args['url'] = url
                    return create_object(self._satellite.cli.Proxy, args, options)
            except CapsuleTunnelError as err:
                raise CLIFactoryError(f'Failed to create ssh tunnel: {err}')
        args['url'] = options['url']
        return create_object(self._satellite.cli.Proxy, args, options)

    def make_template(self, options=None):
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
        self._satellite.put(layout, args['file'])
        # End - Special handling for template factory

        return create_object(self._satellite.cli.Template, args, options)

    def activationkey_add_subscription_to_repo(self, options=None):
        """Helper function that adds subscription to an activation key"""
        # List the subscriptions in given org
        subscriptions = self._satellite.cli.Subscription.list(
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
                    self._satellite.cli.ActivationKey.add_subscription(
                        {
                            'id': options['activationkey-id'],
                            'subscription-id': subscription['id'],
                            'quantity': 1,
                        }
                    )
                except CLIReturnCodeError as err:
                    raise CLIFactoryError(
                        f'Failed to add subscription to activation key\n{err.msg}'
                    )

    def setup_org_for_a_custom_repo(self, options=None):
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
        # Create new organization and lifecycle environment if needed
        if options.get('organization-id') is None:
            org_id = self.make_org()['id']
        else:
            org_id = options['organization-id']
        if options.get('lifecycle-environment-id') is None:
            env_id = self.make_lifecycle_environment({'organization-id': org_id})['id']
        else:
            env_id = options['lifecycle-environment-id']
        # Create custom product and repository
        custom_product = self.make_product({'organization-id': org_id})
        custom_repo = self.make_repository(
            {'content-type': 'yum', 'product-id': custom_product['id'], 'url': options.get('url')}
        )
        # Synchronize custom repository
        try:
            self._satellite.cli.Repository.synchronize({'id': custom_repo['id']})
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to synchronize repository\n{err.msg}')
        # Create CV if needed and associate repo with it
        if options.get('content-view-id') is None:
            cv_id = self.make_content_view({'organization-id': org_id})['id']
        else:
            cv_id = options['content-view-id']
        try:
            self._satellite.cli.ContentView.add_repository(
                {'id': cv_id, 'organization-id': org_id, 'repository-id': custom_repo['id']}
            )
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to add repository to content view\n{err.msg}')
        # Publish a new version of CV
        try:
            self._satellite.cli.ContentView.publish({'id': cv_id})
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to publish new version of content view\n{err.msg}')
        # Get the version id
        cvv = self._satellite.cli.ContentView.info({'id': cv_id})['versions'][-1]
        # Promote version to next env
        try:
            self._satellite.cli.ContentView.version_promote(
                {'id': cvv['id'], 'organization-id': org_id, 'to-lifecycle-environment-id': env_id}
            )
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to promote version to next environment\n{err.msg}')
        # Create activation key if needed and associate content view with it
        if options.get('activationkey-id') is None:
            activationkey_id = self.make_activation_key(
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
                self._satellite.cli.ActivationKey.update(
                    {'content-view-id': cv_id, 'id': activationkey_id, 'organization-id': org_id}
                )
            except CLIReturnCodeError as err:
                raise CLIFactoryError(f'Failed to associate activation-key with CV\n{err.msg}')
        # Add subscription to activation-key
        self.activationkey_add_subscription_to_repo(
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

    def _setup_org_for_a_rh_repo(self, options=None):
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
        # Create new organization and lifecycle environment if needed
        if options.get('organization-id') is None:
            org_id = self.make_org()['id']
        else:
            org_id = options['organization-id']
        if options.get('lifecycle-environment-id') is None:
            env_id = self.make_lifecycle_environment({'organization-id': org_id})['id']
        else:
            env_id = options['lifecycle-environment-id']
        # Clone manifest and upload it
        with manifests.clone() as manifest:
            self._satellite.put(manifest, manifest.filename)
        try:
            self._satellite.cli.Subscription.upload(
                {'file': manifest.filename, 'organization-id': org_id}
            )
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to upload manifest\n{err.msg}')
        # Enable repo from Repository Set
        try:
            self._satellite.cli.RepositorySet.enable(
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
            rhel_repo = self._satellite.cli.Repository.info(
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
            self._satellite.cli.Repository.synchronize(
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
            cv_id = self.make_content_view({'organization-id': org_id})['id']
        else:
            cv_id = options['content-view-id']
        try:
            self._satellite.cli.ContentView.add_repository(
                {'id': cv_id, 'organization-id': org_id, 'repository-id': rhel_repo['id']}
            )
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to add repository to content view\n{err.msg}')
        # Publish a new version of CV
        try:
            self._satellite.cli.ContentView.publish({'id': cv_id})
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to publish new version of content view\n{err.msg}')
        # Get the version id
        try:
            cvv = self._satellite.cli.ContentView.info({'id': cv_id})['versions'][-1]
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to fetch content view info\n{err.msg}')
        # Promote version1 to next env
        try:
            self._satellite.cli.ContentView.version_promote(
                {'id': cvv['id'], 'organization-id': org_id, 'to-lifecycle-environment-id': env_id}
            )
        except CLIReturnCodeError as err:
            raise CLIFactoryError(f'Failed to promote version to next environment\n{err.msg}')
        # Create activation key if needed and associate content view with it
        if options.get('activationkey-id') is None:
            activationkey_id = self.make_activation_key(
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
                self._satellite.cli.ActivationKey.update(
                    {'id': activationkey_id, 'organization-id': org_id, 'content-view-id': cv_id}
                )
            except CLIReturnCodeError as err:
                raise CLIFactoryError(f'Failed to associate activation-key with CV\n{err.msg}')
        # Add subscription to activation-key
        self.activationkey_add_subscription_to_repo(
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

    def setup_org_for_a_rh_repo(
        self, options=None, force_manifest_upload=False, force_use_cdn=False
    ):
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
            return self._setup_org_for_a_rh_repo(options)
        else:
            options['url'] = custom_repo_url
            result = self.setup_org_for_a_custom_repo(options)
            if force_manifest_upload:
                with manifests.clone() as manifest:
                    self._satellite.put(manifest, manifest.filename)
                try:
                    self._satellite.cli.Subscription.upload(
                        {
                            'file': manifest.filename,
                            'organization-id': result.get('organization-id'),
                        }
                    )
                except CLIReturnCodeError as err:
                    raise CLIFactoryError(f'Failed to upload manifest\n{err.msg}')
                # attach the default subscription to activation key
                self.activationkey_add_subscription_to_repo(
                    {
                        'activationkey-id': result['activationkey-id'],
                        'organization-id': result['organization-id'],
                        'subscription': constants.DEFAULT_SUBSCRIPTION_NAME,
                    }
                )
            return result

    def configure_env_for_provision(self, org=None, loc=None):
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
            org = self.make_org()
        if loc is None:
            loc = self.make_location()

        # Get a Library Lifecycle environment and the default CV for the org
        lce = self._satellite.cli.LifecycleEnvironment.info(
            {'name': 'Library', 'organization-id': org['id']}
        )
        cv = self._satellite.cli.ContentView.info(
            {'name': 'Default Organization View', 'organization-id': org['id']}
        )

        # Create puppet environment and associate organization and location
        env = self.make_environment({'location-ids': loc['id'], 'organization-ids': org['id']})

        # get default capsule and associate location
        puppet_proxy = self._satellite.cli.Proxy.info(
            {'id': self._satellite.cli.Proxy.list({'search': settings.server.hostname})[0]['id']}
        )
        self._satellite.cli.Proxy.update(
            {
                'id': puppet_proxy['id'],
                'locations': list(set(puppet_proxy.get('locations') or []) | {loc['name']}),
            }
        )

        # Network
        # Search for existing domain or create new otherwise. Associate org,
        # location and dns to it
        domain_name = settings.server.hostname.partition('.')[-1]
        domain = self._satellite.cli.Domain.list({'search': f'name={domain_name}'})
        if len(domain) == 1:
            domain = self._satellite.cli.Domain.info({'id': domain[0]['id']})
            self._satellite.cli.Domain.update(
                {
                    'name': domain_name,
                    'locations': list(set(domain.get('locations') or []) | {loc['name']}),
                    'organizations': list(set(domain.get('organizations') or []) | {org['name']}),
                    'dns-id': puppet_proxy['id'],
                }
            )
        else:
            # Create new domain
            domain = self.make_domain(
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
        subnet = self._satellite.cli.Subnet.list({'search': f'network={network}'})
        if len(subnet) >= 1:
            subnet = self._satellite.cli.Subnet.info({'id': subnet[0]['id']})
            self._satellite.cli.Subnet.update(
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
            subnet = self.make_subnet(
                {
                    'name': gen_alpha(),
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
        ptable = self._satellite.cli.PartitionTable.info({'name': constants.DEFAULT_PTABLE})

        # Get the OS entity
        os = self._satellite.cli.OperatingSys.list(
            {'search': 'name="RedHat" AND (major="6" OR major="7")'}
        )[0]

        # Get proper Provisioning templates and update with OS, Org, Location
        provisioning_template = self._satellite.cli.Template.info(
            {'name': constants.DEFAULT_TEMPLATE}
        )
        pxe_template = self._satellite.cli.Template.info({'name': constants.DEFAULT_PXE_TEMPLATE})
        for template in provisioning_template, pxe_template:
            if os['title'] not in template['operating-systems']:
                self._satellite.cli.Template.update(
                    {
                        'id': template['id'],
                        'locations': list(set(template.get('locations') or []) | {loc['name']}),
                        'operatingsystems': list(
                            set(template.get('operating-systems') or []) | {os['title']}
                        ),
                        'organizations': list(
                            set(template.get('organizations') or []) | {org['name']}
                        ),
                    }
                )

        # Get the architecture entity
        arch = self._satellite.cli.Architecture.list(
            {'search': f'name={constants.DEFAULT_ARCHITECTURE}'}
        )[0]

        os = self._satellite.cli.OperatingSys.info({'id': os['id']})
        # Get the media and update its location
        medium = self._satellite.cli.Medium.list({'search': f'path={settings.repos.rhel7_os}'})
        if medium:
            media = self._satellite.cli.Medium.info({'id': medium[0]['id']})
            self._satellite.cli.Medium.update(
                {
                    'id': media['id'],
                    'operatingsystems': list(
                        set(media.get('operating-systems') or []) | {os['title']}
                    ),
                    'locations': list(set(media.get('locations') or []) | {loc['name']}),
                    'organizations': list(set(media.get('organizations') or []) | {org['name']}),
                }
            )
        else:
            media = self.make_medium(
                {
                    'location-ids': loc['id'],
                    'operatingsystem-ids': os['id'],
                    'organization-ids': org['id'],
                    'path': settings.repos.rhel7_os,
                }
            )

        # Update the OS with found arch, ptable, templates and media
        self._satellite.cli.OperatingSys.update(
            {
                'id': os['id'],
                'architectures': list(set(os.get('architectures') or []) | {arch['name']}),
                'media': list(set(os.get('installation-media') or []) | {media['name']}),
                'partition-tables': list(set(os.get('partition-tables') or []) | {ptable['name']}),
            }
        )
        for template in (provisioning_template, pxe_template):
            if '{} ({})'.format(template['name'], template['type']) not in os['templates']:
                self._satellite.cli.OperatingSys.update(
                    {
                        'id': os['id'],
                        'provisioning-templates': list(set(os['templates']) | {template['name']}),
                    }
                )

        # Create new hostgroup using proper entities
        hostgroup = self.make_hostgroup(
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
                'root-password': gen_alpha(),
                'content-source-id': puppet_proxy['id'],
            }
        )

        return {
            'hostgroup': hostgroup,
            'subnet': subnet,
            'domain': domain,
            'ptable': ptable,
            'os': os,
        }

    @staticmethod
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

    def add_role_permissions(self, role_id, resource_permissions):
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
        available_permissions = self._satellite.cli.Filter.available_permissions()
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
            self.make_filter(options)

    def setup_cdn_and_custom_repositories(
        self, org_id, repos, download_policy='on_demand', synchronize=True
    ):
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
                self._satellite.cli.RepositorySet.enable(
                    {
                        'organization-id': org_id,
                        'product': repo['product'],
                        'name': repo['repository-set'],
                        'basearch': repo.get('arch', constants.DEFAULT_ARCHITECTURE),
                        'releasever': repo.get('releasever'),
                    }
                )
                repo_info = self._satellite.cli.Repository.info(
                    {
                        'organization-id': org_id,
                        'name': repo['repository'],
                        'product': repo['product'],
                    }
                )
            else:
                if custom_product is None:
                    custom_product = self.make_product_wait({'organization-id': org_id})
                repo_info = self.make_repository(
                    {
                        'product-id': custom_product['id'],
                        'organization-id': org_id,
                        'url': custom_repo_url,
                    }
                )
            if download_policy:
                # Set download policy
                self._satellite.cli.Repository.update(
                    {'download-policy': download_policy, 'id': repo_info['id']}
                )
            repos_info.append(repo_info)
        if synchronize:
            # Synchronize the repositories
            for repo_info in repos_info:
                self._satellite.cli.Repository.synchronize({'id': repo_info['id']}, timeout=4800000)
        return custom_product, repos_info

    def setup_cdn_and_custom_repos_content(
        self,
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

        custom_product, repos_info = self.setup_cdn_and_custom_repositories(
            org_id=org_id, repos=repos, download_policy=download_policy
        )
        if default_cv:
            activation_key = self.make_activation_key(
                {'organization-id': org_id, 'lifecycle-environment': 'Library'}
            )
            content_view = self._satellite.cli.ContentView.info(
                {'organization-id': org_id, 'name': 'Default Organization View'}
            )
        else:
            # Create a content view
            content_view = self.make_content_view({'organization-id': org_id})
            # Add repositories to content view
            for repo_info in repos_info:
                self._satellite.cli.ContentView.add_repository(
                    {
                        'id': content_view['id'],
                        'organization-id': org_id,
                        'repository-id': repo_info['id'],
                    }
                )
            # Publish the content view
            self._satellite.cli.ContentView.publish({'id': content_view['id']})
            # Get the latest content view version id
            content_view_version = self._satellite.cli.ContentView.info({'id': content_view['id']})[
                'versions'
            ][-1]
            # Promote content view version to lifecycle environment
            self._satellite.cli.ContentView.version_promote(
                {
                    'id': content_view_version['id'],
                    'organization-id': org_id,
                    'to-lifecycle-environment-id': lce_id,
                }
            )
            content_view = self._satellite.cli.ContentView.info({'id': content_view['id']})
            activation_key = self.make_activation_key(
                {
                    'organization-id': org_id,
                    'lifecycle-environment-id': lce_id,
                    'content-view-id': content_view['id'],
                }
            )
        # Get organization subscriptions
        subscriptions = self._satellite.cli.Subscription.list(
            {'organization-id': org_id}, per_page=False
        )
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
                self._satellite.cli.ActivationKey.add_subscription(
                    {
                        'id': activation_key['id'],
                        'subscription-id': subscription['id'],
                        'quantity': 1,
                    }
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
            lce = self._satellite.cli.LifecycleEnvironment.info(
                {'id': lce_id, 'organization-id': org_id}
            )
            data['lce'] = lce

        return data
