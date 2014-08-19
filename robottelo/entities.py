"""This module defines all entities which Foreman exposes.

Each class in this module corresponds to a certain type of Foreman entity. For
example, :class:`robottelo.entities.Host` corresponds to the "Host" Foreman
entity. Similarly, each class attribute corresponds to a Foreman entity
attribute. For example, the ``Host.name`` class attribute corresponds to the
"name" attribute of a "Host" entity.

Many of these classes contain an inner class named ``Meta``. This inner class
contains any information about an entity that is not a field. That is, the
inner class contains non-field information. This information is especially
useful to :class:`robottelo.factory.EntityFactoryMixin`.

"""
from robottelo.api import client
from robottelo.common.constants import VALID_GPG_KEY_FILE
from robottelo.common.helpers import get_data_file
from robottelo.common.helpers import get_server_credentials
from robottelo import factory, orm
import time
# (too-few-public-methods) pylint:disable=R0903


class ReadException(Exception):
    """Indicates an error occurred while reading from a Foreman server."""


class TaskTimeout(Exception):
    """If the task is not finished before we reach the timeout."""


class ActivationKey(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Activtion Key entity."""
    organization = orm.OneToOneField('Organization', required=True)
    name = orm.StringField(required=True)
    description = orm.StringField()
    environment = orm.OneToOneField('Environment')
    content_view = orm.OneToOneField('ContentView')
    unlimited_content_hosts = orm.BooleanField()
    max_content_hosts = orm.IntegerField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/activation_keys'

    def path(self, which=None):
        """Extend the default implementation of
        :meth:`robottelo.orm.Entity.path`.

        If a user specifies a ``which`` of ``'releases'``, return a path in the
        format ``/activation_keys/<id>/releases``. Otherwise, call ``super``.

        """
        if which == 'releases':
            return super(ActivationKey, self).path(which='this') + '/releases'
        return super(ActivationKey, self).path()


class Architecture(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Architecture entity."""
    name = orm.StringField(required=True)
    operatingsystems = orm.OneToManyField('OperatingSystem', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/architectures'


class AuthSourceLDAP(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a AuthSourceLDAP entity."""
    name = orm.StringField(required=True, max_len=60)
    host = orm.StringField(required=True, max_len=60)
    # defaults to 389
    port = orm.IntegerField(null=True)
    account = orm.StringField(null=True)
    base_dn = orm.StringField(null=True)
    # required if onthefly_register is true
    account_password = orm.StringField(null=True)
    # required if onthefly_register is true
    attr_login = orm.StringField(null=True)
    # required if onthefly_register is true
    attr_firstname = orm.StringField(null=True)
    # required if onthefly_register is true
    attr_lastname = orm.StringField(null=True)
    # required if onthefly_register is true
    attr_mail = orm.EmailField(null=True)
    attr_photo = orm.StringField(null=True)
    onthefly_register = orm.BooleanField(null=True)
    tls = orm.BooleanField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/auth_source_ldaps'


class Bookmark(orm.Entity):
    """A representation of a Bookmark entity."""
    name = orm.StringField(required=True)
    controller = orm.StringField(required=True)
    query = orm.StringField(required=True)
    public = orm.BooleanField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/bookmarks'


class CommonParameter(orm.Entity):
    """A representation of a Common Parameter entity."""
    name = orm.StringField(required=True)
    value = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/common_parameters'


class ComputeAttribute(orm.Entity):
    """A representation of a Compute Attribute entity."""
    compute_profile = orm.OneToOneField('ComputeProfile', required=True)
    compute_resource = orm.OneToOneField('ComputeResource', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/compute_attributes'
        # Alternative paths:
        #
        # '/api/v2/compute_resources/:compute_resource_id/compute_profiles/'
        # ':compute_profile_id/compute_attributes',
        #
        # '/api/v2/compute_profiles/:compute_profile_id/compute_resources/'
        # ':compute_resource_id/compute_attributes',
        #
        # '/api/v2/compute_resources/:compute_resource_id/'
        # 'compute_attributes',
        #
        # '/api/v2/compute_profiles/:compute_profile_id/compute_attributes',


class ComputeProfile(orm.Entity):
    """A representation of a Compute Profile entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/compute_profiles'


class ComputeResource(orm.Entity):
    """A representation of a Compute Resource entity."""
    name = orm.StringField(null=True)
    # Providers include Libvirt, Ovirt, EC2, Vmware, Openstack,Rackspace, GCE
    provider = orm.StringField(null=True)
    # URL for Libvirt, RHEV, and Openstack
    url = orm.StringField(required=True)
    description = orm.StringField(null=True)
    # Username for RHEV, EC2, Vmware, Openstack. Access Key for EC2
    user = orm.StringField(null=True)
    # Password for RHEV, EC2, Vmware, Openstack. Secret key for EC2
    password = orm.StringField(null=True)
    # for RHEV, Vmware Datacenter
    uuid = orm.StringField(null=True)
    # for EC2 only
    region = orm.StringField(null=True)
    # for Openstack only
    tenant = orm.StringField(null=True)
    # for Vmware
    server = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/compute_resources'


class ConfigGroup(orm.Entity):
    """A representation of a Config Group entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/config_groups'


class ConfigTemplate(orm.Entity):
    """A representation of a Config Template entity."""
    name = orm.StringField(required=True)
    template = orm.StringField(required=True)
    snippet = orm.BooleanField(null=True)
    audit_comment = orm.StringField(null=True)
    # not relevant for snippet
    template_kind = orm.OneToOneField('TemplateKind', null=True)
    # Array of template combinations (hostgroup_id, environment_id)
    template_combinations_attributes = orm.ListField(null=True)  # flake8:noqa pylint:disable=C0103
    # Array of operating systems ID to associate the template with
    operatingsystems = orm.OneToManyField('OperatingSystem', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/config_templates'


class ContentUpload(orm.Entity):
    """A representation of a Content Upload entity."""
    repository = orm.OneToOneField('Repository', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('katello/api/v2/repositories/:repository_id/'
                    'content_uploads')


class ContentViewFilterRule(orm.Entity):
    """A representation of a Content View Filter Rule entity."""
    content_view_filter = orm.OneToOneField('ContentViewFilter', required=True)
    # package or package group: name
    name = orm.StringField()
    # package: version
    version = orm.StringField()
    # package: minimum version
    min_version = orm.StringField()
    # package: maximum version
    max_version = orm.StringField()
    # erratum: id
    errata = orm.OneToOneField('Errata')
    # erratum: start date (YYYY-MM-DD)
    start_date = orm.DateField(fmt='%Y-%m-%d')
    # erratum: end date (YYYY-MM-DD)
    end_date = orm.DateField(fmt='%Y-%m-%d')
    # erratum: types (enhancement, bugfix, security)
    types = orm.ListField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('katello/api/v2/content_view_filters/'
                    ':content_view_filter_id/rules')


class ContentViewFilter(orm.Entity):
    """A representation of a Content View Filter entity."""
    content_view = orm.OneToOneField('ContentView', required=True)
    name = orm.StringField(required=True)
    # type of filter (e.g. rpm, package_group, erratum)
    filter_type = orm.StringField(required=True)
    # Add all packages without Errata to the included/excluded list. (Package
    # Filter only)
    original_packages = orm.BooleanField()
    # specifies if content should be included or excluded, default: false
    inclusion = orm.BooleanField()
    repositories = orm.OneToManyField('Repository')

    class Meta(object):
        """Non-field information about this entity."""
        api_names = (('filter_type', 'type'),)
        api_path = 'katello/api/v2/content_view_filters'
        # Alternative path
        #
        # '/katello/api/v2/content_views/:content_view_id/filters',


class ContentViewPuppetModule(orm.Entity):
    """A representation of a Content View Puppet Module entity."""
    content_view = orm.OneToOneField('ContentView', required=True)
    name = orm.StringField()
    author = orm.StringField()
    uuid = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('katello/api/v2/content_views/:content_view_id/'
                    'content_view_puppet_modules')


class ContentView(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Content View entity."""
    organization = orm.OneToOneField('Organization', required=True)
    name = orm.StringField(required=True)
    label = orm.StringField()
    composite = orm.BooleanField()
    description = orm.StringField()
    repositories = orm.OneToManyField('Repository')
    # List of component content view version ids for composite views
    components = orm.OneToManyField('ContentView')

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/content_views'
        # Alternative paths
        #
        # '/katello/api/v2/organizations/:organization_id/content_views',


class CustomInfo(orm.Entity):
    """A representation of a Custom Info entity."""
    # name of the resource
    informable_type = orm.StringField(required=True)
    # resource identifier
    # FIXME figure out related resource
    # informable = orm.OneToOneField(required=True)
    keyname = orm.StringField(required=True)
    value = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('katello/api/v2/custom_info/:informable_type/'
                    ':informable_id')


class Domain(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Domain entity."""
    # The full DNS Domain name
    name = orm.StringField(required=True)
    # Full name describing the domain
    fullname = orm.StringField(null=True)
    # DNS Proxy to use within this domain
    # FIXME figure out related resource
    # dns = orm.OneToOneField(null=True)
    # Array of parameters (name, value)
    domain_parameters_attributes = orm.ListField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/domains'


class Environment(orm.Entity):
    """A representation of a Environment entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/environments'


class Errata(orm.Entity):
    """A representation of an Errata entity."""
    # You cannot create an errata. Instead, errata are a read-only entity.

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/errata'


class Filter(orm.Entity):
    """A representation of a Filter entity."""
    role = orm.OneToOneField('Role', required=True)
    search = orm.StringField(null=True)
    permissions = orm.OneToManyField('Permission', null=True)
    organizations = orm.OneToManyField('Organization', null=True)
    locations = orm.OneToManyField('Location', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/filters'


def _gpgkey_content():
    """Return default content for a GPG key.

    :return: The contents of a GPG key.
    :rtype: str

    """
    with open(get_data_file(VALID_GPG_KEY_FILE)) as handle:
        return handle.read()


class GPGKey(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a GPG Key entity."""
    organization = orm.OneToOneField('Organization', required=True)
    # identifier of the gpg key
    # validator: string from 2 to 128 characters containting only alphanumeric
    # characters, space, '_', '-' with no leading or trailing space.
    name = orm.StringField(required=True)
    # public key block in DER encoding
    content = orm.StringField(required=True, default=_gpgkey_content())

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/gpg_keys'


class HostClasses(orm.Entity):
    """A representation of a Host Class entity."""
    host = orm.OneToOneField('Host', required=True)
    puppetclass = orm.OneToOneField('PuppetClass', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/hosts/:host_id/puppetclass_ids'


class HostCollectionErrata(orm.Entity):
    """A representation of a Host Collection Errata entity."""
    errata = orm.OneToManyField('Errata', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('katello/api/v2/organizations/:organization_id/'
                    'host_collections/:host_collection_id/errata')


class HostCollectionPackage(orm.Entity):
    """A representation of a Host Collection Package entity."""
    packages = orm.ListField()
    groups = orm.ListField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('katello/api/v2/organizations/:organization_id/'
                    'host_collections/:host_collection_id/packages')


class HostCollection(orm.Entity):
    """A representation of a Host Collection entity."""
    organization = orm.OneToOneField('Organization', required=True)
    # List of system uuids to replace the content hosts in host collection
    system_uuids = orm.ListField()
    name = orm.StringField(required=True)
    # List of system uuids to be in the host collection
    system = orm.OneToManyField('System')
    description = orm.StringField()
    # Maximum number of content hosts in the host collection
    max_content_hosts = orm.IntegerField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/host_collections'
        # Alternative paths.
        #
        # '/katello/api/v2/organizations/:organization_id/host_collections'


class HostGroupClasses(orm.Entity):
    """A representation of a Host Group Classes entity."""
    hostgroup = orm.OneToOneField('HostGroup', required=True)
    puppetclass = orm.OneToOneField('PuppetClass', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/hostgroups/:hostgroup_id/puppetclass_ids'


class HostGroup(orm.Entity):
    """A representation of a Host Group entity."""
    name = orm.StringField(required=True)
    parent = orm.OneToOneField('HostGroup', null=True)
    environment = orm.OneToOneField('Environment', null=True)
    operatingsystem = orm.OneToOneField('OperatingSystem', null=True)
    architecture = orm.OneToOneField('Architecture', null=True)
    medium = orm.OneToOneField('Media', null=True)
    ptable = orm.OneToOneField('PartitionTable', null=True)
    # FIXME figure out related resource
    # puppet_ca_proxy = orm.OneToOneField(null=True)
    subnet = orm.OneToOneField('Subnet', null=True)
    domain = orm.OneToOneField('Domain', null=True)
    realm = orm.OneToOneField('Realm', null=True)
    # FIXME figure out related resource
    # puppet_proxy = orm.OneToOneField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/hostgroups'


class Host(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Host entity."""
    name = orm.StringField(required=True)
    environment = orm.OneToOneField('Environment', null=True)
    # not required if using a subnet with dhcp proxy
    ip = orm.StringField(null=True)  # (invalid-name) pylint:disable=C0103
    # not required if its a virtual machine
    mac = orm.StringField(null=True)
    architecture = orm.OneToOneField('Architecture', null=True)
    domain = orm.OneToOneField('Domain', null=True)
    realm = orm.OneToOneField('Realm', null=True)
    # FIXME figure out related resource
    # puppet_proxy = orm.OneToOneField(null=True)
    puppet_classes = orm.OneToManyField('PuppetClass', null=True)
    operatingsystem = orm.OneToOneField('OperatingSystem', null=True)
    medium = orm.OneToOneField('Media', null=True)
    ptable = orm.OneToOneField('PartitionTable', null=True)
    subnet = orm.OneToOneField('Subnet', null=True)
    compute_resource = orm.OneToOneField('ComputeResource', null=True)
    sp_subnet = orm.OneToOneField('Subnet', null=True)
    model = orm.OneToOneField('Model', null=True)
    hostgroup = orm.OneToOneField('HostGroup', null=True)
    owner = orm.OneToOneField('User', null=True)
    # FIXME figure out related resource
    # puppet_ca_proxy = orm.OneToOneField(null=True)
    image = orm.OneToOneField('Image', null=True)
    host_parameters_attributes = orm.ListField(null=True)
    build = orm.BooleanField(null=True)
    enabled = orm.BooleanField(null=True)
    provision_method = orm.StringField(null=True)
    managed = orm.BooleanField(null=True)
    # UUID to track orchestration tasks status,
    # GET /api/v2/orchestration/:UUID/tasks
    # FIXME figure out related resource
    # progress_report = orm.OneToOneField(null=True)
    capabilities = orm.StringField(null=True)
    compute_profile = orm.OneToOneField('ComputeProfile', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_names = (('name', 'name'),)
        api_path = 'api/v2/hosts'


class Image(orm.Entity):
    """A representation of a Image entity."""
    compute_resource = orm.OneToOneField('ComputeResource', required=True)
    name = orm.StringField(required=True)
    username = orm.StringField(required=True)
    uuid = orm.StringField(required=True)
    architecture = orm.OneToOneField('Architecture', required=True)
    operatingsystem = orm.OneToOneField('OperatingSystem', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/compute_resources/:compute_resource_id/images'


class Interface(orm.Entity):
    """A representation of a Interface entity."""
    host = orm.OneToOneField('Host', required=True)
    mac = orm.MACAddressField(required=True)
    ip = orm.IPAddressField(required=True)  # pylint:disable=C0103
    # Interface type, i.e: Nic::BMC
    interface_type = orm.StringField(required=True)
    name = orm.StringField(required=True)
    subnet = orm.OneToOneField('Subnet', null=True)
    domain = orm.OneToOneField('Domain', null=True)
    username = orm.StringField(null=True)
    password = orm.StringField(null=True)
    # Interface provider, i.e: IPMI
    provider = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_names = (('interface_type', 'type'),)
        api_path = 'api/v2/hosts/:host_id/interfaces'


class LifecycleEnvironment(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Lifecycle Environment entity."""
    organization = orm.OneToOneField('Organization', required=True)
    name = orm.StringField(required=True)
    description = orm.StringField()
    # A prior environment in a tree of lifecycle environments. The root of the
    # tree has name of 'Library' and no value in this field.
    # FIXME: This field is not required. Remove `required` and update other
    # methods to deal with the change.
    prior = orm.OneToOneField('LifecycleEnvironment', required=True)

    def _factory_data(self):
        """Extend the default implementation of
        :meth:`robottelo.factory.EntityFactoryMixin._factory_data`.

        Since a ``LifecycleEnvironment`` can be associated to another instance
        of a ``LifecycleEnvironment`` via the ``prior`` field, the expected
        foreignkey is not ``prior_id`` as expected, but ``prior``. Therefore, we
        must update the entity's fields and make sure that we have a ``prior``
        attribute before any further actions can be performed.

        """
        lc_attrs = super(LifecycleEnvironment, self)._factory_data()
        # Add ``prior`` back into the fields
        lc_attrs['prior'] = lc_attrs.pop('prior_id')
        return lc_attrs

    def build(self, auth=None):
        """Extend the implementation of :meth:`robottelo.factory.Factory.build`.

        When a new lifecycle environment is created, it must either:

        * Reference some other lifecycle environment via the "prior" field.
        * Have a name of "Library". Note that within a given organization, there
          can only be a single lifecycle environment with a name of "Library".

        This method does the following:

        1. If this entity does not yet point to an organization (i.e. if
           ``self.organization is None``), an organization is created.
        2. If this entity does not yet point to another lifecycle entity (i.e.
           if ``self.prior is None``), the "Library" lifecycle environment for
           this lifecycle environment's organization is found and used.

        """
        if self.organization is None:
            self.organization = Organization().create(auth=auth)['id']
        if self.prior is None:
            query_results = client.get(
                self.path(),
                auth=get_server_credentials(),
                verify=False,
                params={
                    'name': 'Library',
                    'organization_id': self.organization,
                }
            ).json()['results']
            if len(query_results) != 1:
                raise factory.FactoryError(
                    'Could not find the "Library" lifecycle environment for '
                    'organization {0}. Search returned {1} results.'
                    ''.format(self.organization, len(query_results))
                )
            self.prior = query_results[0]['id']
        return super(LifecycleEnvironment, self).build(auth)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/environments'


class Location(orm.Entity):
    """A representation of a Location entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/locations'


class Media(orm.Entity):
    """A representation of a Media entity."""
    # Name of media
    # validator: String
    name = orm.StringField(required=True)
    # The path to the medium, can be a URL or a valid NFS server (exclusive of
    # the architecture). for example
    # mirror.centos.org/centos/$version/os/$arch where $arch will be
    # substituted for the host's actual OS architecture and $version, $major
    # and $minor will be substituted for the version of the operating system.
    # Solaris and Debian media may also use $release.
    path = orm.StringField(required=True)
    # The family that the operating system belongs to.
    # Available families: AIX, Archlinux, Debian, Freebsd, Gentoo, Junos,
    # Redhat, Solaris, Suse, Windows
    os_family = orm.StringField(choices=(
        'AIX', 'Archlinux', 'Debian', 'Freebsd', 'Gentoo', 'Junos', 'Redhat',
        'Solaris', 'Suse', 'Windows',
    ), null=True)
    operatingsystems = orm.OneToManyField('OperatingSystem', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/media'


class Model(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Model entity."""
    name = orm.StringField(required=True)
    info = orm.StringField(null=True)
    vendor_class = orm.StringField(null=True)
    hardware_model = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/models'


class OperatingSystem(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Operating System entity.

    ``major`` is listed as a string field in the API docs, but only numeric
    values are accepted, and they may be no longer than 5 digits long. Also see
    bugzilla bug #1122261.

    """
    # validator: Must match regular expression /\A(\S+)\Z/.
    name = orm.StringField(required=True)
    major = orm.StringField(required=True, str_type=('numeric',), max_len=5)
    minor = orm.StringField(null=True)
    description = orm.StringField(null=True)
    family = orm.StringField(null=True)
    release_name = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/operatingsystems'


class OrganizationDefaultInfo(orm.Entity):
    """A representation of a Organization Default Info entity."""
    # name of the resource
    informable_type = orm.StringField(required=True)
    # resource identifier
    # FIXME figure out related resource
    # informable = orm.OneToOneField(required=True)
    keyname = orm.StringField(required=True)
    name = orm.StringField(required=True)
    info = orm.StringField()
    vendor_class = orm.StringField()
    hardware_model = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('katello/api/v2/organizations/:organization_id/'
                    'default_info/:informable_type')


class Organization(orm.Entity, factory.EntityFactoryMixin):
    """A representation of an Organization entity."""
    name = orm.StringField(required=True)
    label = orm.StringField()
    description = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/organizations'


class OSDefaultTemplate(orm.Entity):
    """A representation of a OS Default Template entity."""
    operatingsystem = orm.OneToOneField('OperatingSystem')
    template_kind = orm.OneToOneField('TemplateKind', null=True)
    config_template = orm.OneToOneField('ConfigTemplate', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('api/v2/operatingsystems/:operatingsystem_id/'
                    'os_default_templates')


class OverrideValue(orm.Entity):
    """A representation of a Override Value entity."""
    smart_variable = orm.OneToOneField('SmartVariable')
    match = orm.StringField(null=True)
    value = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        # FIXME: This is tricky. Overriding path() may be a solution.
        api_path = (
            # Create an override value for a specific smart_variable
            '/api/v2/smart_variables/:smart_variable_id/override_values',
            # Create an override value for a specific smart class parameter
            '/api/v2/smart_class_parameters/:smart_class_parameter_id/'
            'override_values',
        )


class Parameter(orm.Entity):
    """A representation of a Parameter entity."""
    host = orm.OneToOneField('Host')
    hostgroup = orm.OneToOneField('HostGroup')
    domain = orm.OneToOneField('Domain')
    operatingsystem = orm.OneToOneField('OperatingSystem')
    location = orm.OneToOneField('Location')
    organization = orm.OneToOneField('Organization')
    name = orm.StringField(required=True)
    value = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/hosts/:host_id/parameters'
        # Alternative paths.
        #
        # '/api/v2/hostgroups/:hostgroup_id/parameters'
        # '/api/v2/domains/:domain_id/parameters'
        # '/api/v2/operatingsystems/:operatingsystem_id/parameters'
        # '/api/v2/locations/:location_id/parameters'
        # '/api/v2/organizations/:organization_id/parameters'


class Permission(orm.Entity):
    """A representation of a Permission entity."""
    description = orm.StringField(null=True)
    name = orm.StringField(required=True)
    organization = orm.OneToOneField('Organization')
    # array of tag ids
    tags = orm.ListField()
    # name of a resource or 'all'
    permission_type = orm.StringField(required=True)
    # array of permission verbs
    verbs = orm.ListField()
    # True if the permission should use all tags
    all_tags = orm.BooleanField()
    # True if the permission should use all verbs
    all_verbs = orm.BooleanField()

    class Meta(object):
        """Non-field information about this entity."""
        api_names = (('permission_type', 'type'),)
        api_path = 'katello/api/v2/roles/:role_id/permissions'


class Ping(orm.Entity):
    """A representation of a Ping entity."""

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/ping'


class Product(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Product entity."""
    organization = orm.OneToOneField('Organization', required=True)
    description = orm.StringField()
    gpg_key = orm.OneToOneField('GPGKey')
    sync_plan = orm.OneToOneField('SyncPlan', null=True)
    name = orm.StringField(required=True)
    label = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/products'


class PartitionTable(orm.Entity):
    """A representation of a Partition Table entity."""
    name = orm.StringField(required=True)
    layout = orm.StringField(required=True)
    os_family = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/ptables'


class PuppetClass(orm.Entity):
    """A representation of a Puppet Class entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/puppetclasses'


class Realm(orm.Entity):
    """A representation of a Realm entity."""
    # The realm name, e.g. EXAMPLE.COM
    name = orm.StringField(required=True)
    # Proxy to use for this realm
    # FIXME figure out related resource
    # realm_proxy = orm.OneToOneField(null=True)
    # Realm type, e.g. Red Hat Identity Management or Active Directory
    realm_type = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/realms'


class Report(orm.Entity):
    """A representation of a Report entity."""
    # Hostname or certname
    host = orm.StringField(required=True)
    # UTC time of report
    reported_at = orm.DateTimeField(required=True)
    # Optional array of log hashes
    logs = orm.ListField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/reports'


class Repository(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Repository entity."""
    name = orm.StringField(required=True)
    label = orm.StringField()
    # Product the repository belongs to
    product = orm.OneToOneField('Product', required=True)
    # repository source url
    url = orm.URLField(required=True)
    # id of the gpg key that will be assigned to the new repository
    gpg_key = orm.OneToOneField('GPGKey')
    # true if this repository can be published via HTTP
    unprotected = orm.BooleanField()
    # type of repo (either 'yum' or 'puppet', defaults to 'yum')
    content_type = orm.StringField(
        choices=('puppet', 'yum', 'file'),
        default='yum',
        required=True,
    )

    def path(self, which=None):
        """Extend the default implementation of
        :meth:`robottelo.orm.Entity.path`.

        If a user specifies a ``which`` of ``'sync'``, return a path in the
        format ``/repositories/<id>/sync``. Otherwise, call ``super``.

        """
        if which == 'sync':
            return super(Repository, self).path(which='this') + '/sync'
        return super(Repository, self).path()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/repositories'


class RoleLDAPGroups(orm.Entity):
    """A representation of a Role LDAP Groups entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/roles/:role_id/ldap_groups'


class Role(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Role entity."""
    # FIXME: UTF-8 characters should be acceptable for `name`. See BZ 1129785
    name = orm.StringField(required=True, str_type=('alphanumeric',))

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/roles'


class SmartProxy(orm.Entity):
    """A representation of a Smart Proxy entity."""
    name = orm.StringField(required=True)
    url = orm.URLField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/smart_proxies'


class SmartVariable(orm.Entity):
    """A representation of a Smart Variable entity."""
    variable = orm.StringField(required=True)
    puppetclass = orm.OneToOneField('PuppetClass', null=True)
    default_value = orm.StringField(null=True)
    override_value_order = orm.StringField(null=True)
    description = orm.StringField(null=True)
    validator_type = orm.StringField(null=True)
    validator_rule = orm.StringField(null=True)
    variable_type = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/smart_variables'


class Status(orm.Entity):
    """A representation of a Status entity."""

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/status'


class Subnet(orm.Entity):
    """A representation of a Subnet entity."""
    name = orm.StringField(required=True)
    network = orm.IPAddressField(required=True)
    mask = orm.IPAddressField(required=True)
    gateway = orm.StringField(null=True)
    dns_primary = orm.IPAddressField(null=True)
    dns_secondary = orm.IPAddressField(null=True)
    # Starting IP Address for IP auto suggestion
    from_ip = orm.IPAddressField(null=True)
    # Ending IP Address for IP auto suggestion
    to_ip = orm.IPAddressField(null=True)
    # VLAN ID for this subnet
    vlanid = orm.StringField(null=True)
    # Domains in which this subnet is part
    domain = orm.OneToManyField('Domain', null=True)
    # DHCP Proxy to use within this subnet
    # FIXME figure out related resource
    # dhcp = orm.OneToOneField(null=True)
    # TFTP Proxy to use within this subnet
    # FIXME figure out related resource
    # tftp = orm.OneToOneField(null=True)
    # DNS Proxy to use within this subnet
    # FIXME figure out related resource
    # dns = orm.OneToOneField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/subnets'


class Subscription(orm.Entity):
    """A representation of a Subscription entity."""
    # Subscription Pool uuid
    pool_uuid = orm.StringField()
    # UUID of the system
    system = orm.OneToOneField('System')
    activation_key = orm.OneToOneField('ActivationKey')
    # Quantity of this subscriptions to add
    quantity = orm.IntegerField()
    subscriptions = orm.OneToManyField('Subscription')

    class Meta(object):
        """Non-field information about this entity."""
        api_names = (('pool_uuid', 'id'),)
        api_path = 'katello/api/v2/subscriptions/:id'
        # Alternative paths.
        #
        # '/katello/api/v2/systems/:system_id/subscriptions',
        # '/katello/api/v2/activation_keys/:activation_key_id/subscriptions',


class SyncPlan(orm.Entity):
    """A representation of a Sync Plan entity."""
    organization = orm.OneToOneField('Organization', required=True)
    name = orm.StringField(required=True)
    # how often synchronization should run must be one of: none, hourly, daily,
    # weekly.
    interval = orm.StringField(
        choices=('none', 'hourly', 'daily', 'weekly'),
        required=True,
    )
    # start datetime of synchronization
    sync_date = orm.DateTimeField(required=True)
    description = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/organizations/:organization_id/sync_plans'


class SystemPackage(orm.Entity):
    """A representation of a System Package entity."""
    system = orm.OneToOneField('System', required=True)
    # List of package names
    packages = orm.ListField()
    # List of package group names
    groups = orm.ListField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'katello/api/v2/systems/:system_id/packages'


class System(orm.Entity):
    """A representation of a System entity."""
    name = orm.StringField(required=True)
    description = orm.StringField()
    # Physical location of the content host
    location = orm.StringField()
    # Any number of facts about this content host
    fact = orm.StringField(null=True)
    # Type of the content host, it should always be 'content host'
    system_type = orm.StringField(default='content host', required=True)
    # IDs of the guests running on this content host
    # FIXME figure out related resource
    # guest = orm.OneToManyField()
    # List of products installed on the content host
    installed_products = orm.ListField(null=True)
    # Release version of the content host
    release_ver = orm.StringField()
    # A service level for auto-healing process, e.g. SELF-SUPPORT
    service_level = orm.StringField(null=True)
    # Last check-in time of this content host
    last_checkin = orm.DateTimeField()
    organization = orm.OneToOneField('Organization', required=True)
    environment = orm.OneToOneField('Environment')
    content_view = orm.OneToOneField('ContentView')
    host_collection = orm.OneToOneField('HostCollection')

    class Meta(object):
        """Non-field information about this entity."""
        api_names = (('system_type', 'type'),)
        api_path = 'katello/api/v2/systems'
        # Alternative paths.
        # '/katello/api/v2/environments/:environment_id/systems'
        # '/katello/api/v2/host_collections/:host_collection_id/systems'


class ForemanTask(orm.Entity):
    """A representation of a Foreman task."""

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'foreman_tasks/api/tasks'

    def path(self, which=None):
        """Override the default implementation of
        :meth:`robottelo.orm.Entity.path`.

        There is no available path for fetching all Foreman tasks. Instead, the
        user must either:

        * fetch a specific task by providing a UUID via the ``id`` instance
          attribute, or
        * perform a bulk search.

        Thus, this method returns a slightly unusual set of paths:

        * Return the path ``/foreman_tasks/api/tasks/bulk_search`` if the user
          specifies ``which = 'bulk_search'``.
        * Return a path in the format ``/foreman_tasks/api/tasks/<id>``
          otherwise.

        """
        if which == 'bulk_search':
            return '{0}/bulk_search'.format(
                super(ForemanTask, self).path(which='all')
            )
        return super(ForemanTask, self).path(which='this')

    def read(self, auth=None):
        """Return information about a foreman task.

        :return: Information about this foreman task.
        :rtype: dict
        :raises ReadException: If information about this foreman task could not
            be fetched. This could happen if, for example, the task does not
            exist or bad credentials are used.

        """
        # FIXME: Need better error handling. If there's an authentication
        # error, the server will respond with JSON:
        #
        #     {u'error': {u'text': u'Unable to authenticate user.'}}
        #
        # But what if the JSON response contains 'errors', or what if the
        # response cannot be converted to JSON at all? A utility function can
        # probably be created for this need. Perhaps
        # robottelo.api.utils.status_code_error() could be of use. After all,
        # most of that method is devoted to fetching an error message, and only
        # the last bit composes an error message.
        if auth is None:
            auth = get_server_credentials()
        response = client.get(self.path(), auth=auth, verify=False)
        if response.status_code is not 200:
            raise ReadException(response.text)
        if response.json() == {}:
            # FIXME: See bugzilla bug #1131702
            raise ReadException(
                'ForemanTask {0} does not exist.'.format(self.id)
            )
        return response.json()

    def poll(self, poll_rate=5, timeout=120, auth=None):
        """Return the status of a task or timeout.

        There are several API calls that trigger asynchronous tasks, such as
        synchronizing a repository or publishing/promoting a content view.
        These tasks should always return a `uuid` which then can be used to
        poll and check on its status. This method checks the status for a
        given `uuid` at `poll_rate` intervals until said task is no longer
        pending. If it takes longer than `timeout`

        :param int poll_rate: How often to check the status of a task in
            seconds.
        :param int timeout: Maximum number of seconds to wait until we
            timeout.
        :param tuple auth: A ``(username, password)`` pair to use when
            communicating with the API. If ``None``, the credentials returned
            by :func:`robottelo.common.helpers.get_server_credentials` are
            used.
        :return: Information about the asynchronous task.
        :rtype: dict
        :raises robottelo.entities.TaskTimeOut: If the task is not finished
            before we reach the timeout.

        """
        if auth is None:
            auth = get_server_credentials()

        timeout = time.time() + timeout
        task_status = self.read(auth=auth)

        while task_status['pending'] == True and time.time() < timeout:
            time.sleep(poll_rate)
            task_status = self.read(auth=auth)

        # Are we done? If so, return.
        if task_status['pending'] == False:
            return task_status
        else:
            raise TaskTimeout("Timed out polling task {0}".format(self.id))


class TemplateCombination(orm.Entity):
    """A representation of a Template Combination entity."""
    config_template = orm.OneToOneField('ConfigTemplate', required=True)
    environment = orm.OneToOneField('Environment', null=True)
    hostgroup = orm.OneToOneField('HostGroup', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = ('api/v2/config_templates/:config_template_id/'
                    'template_combinations')


class TemplateKind(orm.Entity):
    """A representatio of a Template Kind entity."""
    # FIXME figure out fields


class UserGroup(orm.Entity):
    """A representation of a User Group entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/usergroups'


class User(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a User entity.

    The LDAP authentication source with an ID of 1 is internal. It is nearly
    guaranteed to exist and be functioning. Thus, ``auth_source`` is set to "1"
    by default for a practical reason: it is much easier to use internal
    authentication than to spawn LDAP authentication servers for each new user.

    """
    login = orm.StringField(
        required=True,
        # Passing UTF8 characters to ``login`` yields 500s.
        str_type=('alpha', 'alphanumeric', 'cjk', 'latin1'))
    firstname = orm.StringField(null=True, max_len=60)
    lastname = orm.StringField(null=True, max_len=60)
    mail = orm.EmailField(required=True)
    # Is an admin account?
    admin = orm.BooleanField(null=True)
    password = orm.StringField(required=True)
    default_location = orm.OneToOneField('Location', null=True)
    default_organization = orm.OneToOneField('Organization', null=True)
    auth_source = orm.OneToOneField('AuthSourceLDAP', default=1, required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = 'api/v2/users'
