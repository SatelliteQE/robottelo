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
from robottelo import factory, orm
# (too-few-public-methods) pylint:disable=R0903


class ActivationKey(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Activtion Key entity."""
    organization = orm.OneToOneField('Organization', required=True)
    name = orm.StringField(required=True)
    description = orm.StringField()
    environment = orm.OneToOneField('LifecycleEnvironment')
    content_view = orm.OneToOneField('ContentView')
    # maximum number of registered content hosts, or 'unlimited'
    usage_limit = orm.IntegerField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/activation_keys',  # Create an activation key
        )


class Architecture(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Architecture entity."""
    name = orm.StringField(required=True)
    operatingsystems = orm.OneToManyField('OperatingSystem', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/architectures',  # Create an architecture.
        )


class AuthSourceLDAP(orm.Entity):
    """A representation of a AuthSourceLDAP entity."""
    name = orm.StringField(required=True)
    host = orm.StringField(required=True)
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
    attr_mail = orm.StringField(null=True)
    attr_photo = orm.StringField(null=True)
    onthefly_register = orm.BooleanField(null=True)
    tls = orm.BooleanField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/auth_source_ldaps',  # Create an auth_source_ldap.
        )


class Bookmark(orm.Entity):
    """A representation of a Bookmark entity."""
    name = orm.StringField(required=True)
    controller = orm.StringField(required=True)
    query = orm.StringField(required=True)
    public = orm.BooleanField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/bookmarks',  # Create a bookmark.
        )


class CommonParameter(orm.Entity):
    """A representation of a Common Parameter entity."""
    name = orm.StringField(required=True)
    value = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/common_parameters',  # Create a common_parameter
        )


class ComputeAttribute(orm.Entity):
    """A representation of a Compute Attribute entity."""
    compute_profile = orm.OneToOneField('ComputeProfile', required=True)
    compute_resource = orm.OneToOneField('ComputeResource', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Create a compute attribute.
            '/api/v2/compute_resources/:compute_resource_id/compute_profiles/'
            ':compute_profile_id/compute_attributes',
            # Create a compute attribute.
            '/api/v2/compute_profiles/:compute_profile_id/compute_resources/'
            ':compute_resource_id/compute_attributes',
            # Create a compute attribute.
            '/api/v2/compute_resources/:compute_resource_id/'
            'compute_attributes',
            # Create a compute attribute.
            '/api/v2/compute_profiles/:compute_profile_id/compute_attributes',
            # Create a compute attribute.
            '/api/v2/compute_attributes',
        )


class ComputeProfile(orm.Entity):
    """A representation of a Compute Profile entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/compute_profiles',  # Create a compute profile.
        )


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
        api_path = (
            '/api/v2/compute_resources',  # Create a compute resource.
        )


class ConfigGroup(orm.Entity):
    """A representation of a Config Group entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/config_groups',  # Create a config group.
        )


class ConfigTemplate(orm.Entity):
    """A representation of a Config Template entity."""
    name = orm.StringField(required=True)
    template = orm.StringField(required=True)
    snippet = orm.BooleanField(null=True)
    audit_comment = orm.StringField(null=True)
    # not relevant for snippet
    template_kind = orm.OneToOneField('TemplateKind', null=True)
    # Array of template combinations (hostgroup_id, environment_id)
    template_combinations_attributes = orm.ListField(null=True)
    # Array of operating systems ID to associate the template with
    operatingsystems = orm.OneToManyField('OperatingSystem', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/config_templates',  # Create a template
        )


class ContentUpload(orm.Entity):
    """A representation of a Content Upload entity."""
    repository = orm.OneToOneField('Repository', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Create an upload request
            '/katello/api/v2/repositories/:repository_id/content_uploads',
        )


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
        api_path = (
            # Create a filter rule. The parameters included should be based
            # upon the filter type.
            '/katello/api/v2/content_view_filters/:content_view_filter_id/'
            'rules',
        )


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
        api_path = (
            # Create a filter for a content view
            '/katello/api/v2/content_views/:content_view_id/filters',
            # Create a filter for a content view
            '/katello/api/v2/content_view_filters',
        )


class ContentViewPuppetModule(orm.Entity):
    """A representation of a Content View Puppet Module entity."""
    content_view = orm.OneToOneField('ContentView', required=True)
    name = orm.StringField()
    author = orm.StringField()
    uuid = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Add a puppet module to the content view
            '/katello/api/v2/content_views/:content_view_id/'
            'content_view_puppet_modules',
        )


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
        api_path = (
            # Create a content view
            '/katello/api/v2/content_views',
            # Create a content view
            '/katello/api/v2/organizations/:organization_id/content_views',
        )


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
        api_path = (
            # Create custom info
            '/katello/api/v2/custom_info/:informable_type/:informable_id',
        )


class Domain(orm.Entity):
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
        api_path = (
            '/api/v2/domains',  # Create a domain.
        )


class Environment(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Environment entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/environments',  # Create an environment.
        )


class Filter(orm.Entity):
    """A representation of a Filter entity."""
    role = orm.OneToOneField('Role', required=True)
    search = orm.StringField(null=True)
    permissions = orm.OneToManyField('Permission', null=True)
    organizations = orm.OneToManyField('Organization', null=True)
    locations = orm.OneToManyField('Location', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/filters',  # Create a filter.
        )


class GPGKey(orm.Entity):
    """A representation of a GPG Key entity."""
    organization = orm.OneToOneField('Organization', required=True)
    # identifier of the gpg key
    # validator: string from 2 to 128 characters containting only alphanumeric
    # characters, space, '_', '-' with no leading or trailing space.
    name = orm.StringField(required=True)
    # public key block in DER encoding
    content = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/gpg_keys',  # Create a gpg key
        )


class HostClasses(orm.Entity):
    """A representation of a Host Class entity."""
    host = orm.OneToOneField('Host', required=True)
    puppetclass = orm.OneToOneField('PuppetClass', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Add a puppetclass to host
            '/api/v2/hosts/:host_id/puppetclass_ids',
        )


class HostCollectionErrata(orm.Entity):
    """A representation of a Host Collection Errata entity."""
    errata = orm.OneToManyField('Errata', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/organizations/:organization_id/host_collections/'
            ':host_collection_id/errata',  # Install errata remotely
        )


class HostCollectionPackage(orm.Entity):
    """A representation of a Host Collection Package entity."""
    packages = orm.ListField()
    groups = orm.ListField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/organizations/:organization_id/host_collections/'
            ':host_collection_id/packages',  # Install packages remotely
        )


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
        api_path = (
            # Create a host collection
            '/katello/api/v2/host_collections',
            # Create a host collection
            '/katello/api/v2/organizations/:organization_id/host_collections',
        )


class HostGroupClasses(orm.Entity):
    """A representation of a Host Group Classes entity."""
    hostgroup = orm.OneToOneField('HostGroup', required=True)
    puppetclass = orm.OneToOneField('PuppetClass', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Add a puppetclass to hostgroup
            '/api/v2/hostgroups/:hostgroup_id/puppetclass_ids',
        )


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
        api_path = (
            '/api/v2/hostgroups',  # Create an hostgroup.
        )


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
        api_names = (('name', 'host[name]'),)
        api_path = (
            '/api/v2/hosts',  # Create a host.
        )


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
        api_path = (
            # Create a image
            '/api/v2/compute_resources/:compute_resource_id/images',
        )


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
        api_path = (
            # Create an interface linked to a host
            '/api/v2/hosts/:host_id/interfaces',
        )


class LifecycleEnvironment(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Lifecycle Environment entity."""
    organization = orm.OneToOneField('Organization', required=True)
    name = orm.StringField(required=True)
    description = orm.StringField()
    # ID of an environment that is prior to the new environment in the chain.
    # It has to be either 'Library' or an environment at the end of a chain.
    prior = orm.StringField(default='1', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Create an environment
            '/katello/api/v2/environments',
            # Create an environment in an organization
            '/katello/api/v2/organizations/:organization_id/environments',
        )


class Location(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Location entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/locations',  # Create a location
        )


class Media(orm.Entity, factory.EntityFactoryMixin):
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
    # The family that the operating system belongs to.
    path = orm.URLField(required=True)
    # Available families: AIX, Archlinux, Debian, Freebsd, Gentoo, Junos,
    # Redhat, Solaris, Suse, Windows
    os_family = orm.StringField(choices=(
        'AIX', 'Archlinux', 'Debian', 'Freebsd', 'Gentoo', 'Junos', 'Redhat',
        'Solaris', 'Suse', 'Windows',
    ), null=True)
    operatingsystems = orm.OneToManyField('OperatingSystem', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/media',  # Create a medium.
        )


class Model(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Model entity."""
    name = orm.StringField(max_len=255, required=True)
    info = orm.StringField(null=True)
    vendor_class = orm.StringField(null=True)
    hardware_model = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/models',  # Create a model.
        )

    def _unpack_response(self, response):
        """Unpack the server's response after creating an entity."""
        return response['model']


class OperatingSystem(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Operating System entity."""
    # validator: Must match regular expression /\A(\S+)\Z/.
    name = orm.StringField(required=True)
    major = orm.IntegerField(min_val=1, max_val=10, required=True)
    minor = orm.IntegerField(null=True)
    description = orm.StringField(null=True)
    family = orm.StringField(null=True)
    release_name = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/operatingsystems',  # Create an OS.
        )


class OrganizationDefaultInfo(orm.Entity):
    """A representation of a Organization Default Info entity."""
    # name of the resource
    informable_type = orm.StringField(required=True)
    # resource identifier
    # FIXME figure out related resource
    # informable = orm.OneToOneField(required=True)
    keyname = orm.StringField(required=True)
    name = orm.ShortStringField(required=True)
    info = orm.StringField()
    vendor_class = orm.StringField()
    hardware_model = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/organizations/:organization_id/default_info/'
            ':informable_type',  # Create default info
        )
        # FIXME: is this mapping correct?
        api_names = (
            ('name', 'model[name]'),
            ('info', 'model[info]'),
            ('vendor_class', 'model[vendor_class]'),
            ('hardware_model', 'model[hardware_model]'),
        )

    def _unpack_response(self, response):  # (no-self-use) pylint:disable=R0201
        """Unpack the server's response after creating an entity."""
        return response['model']


class Organization(orm.Entity, factory.EntityFactoryMixin):
    """A representation of an Organization entity."""
    name = orm.StringField(required=True)
    label = orm.StringField()
    description = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/organizations',  # Create organization
        )

    def _unpack_response(self, response):  # (no-self-use) pylint:disable=R0201
        """Unpack the server's response after creating an entity."""
        return response['organization']


class OSDefaultTemplate(orm.Entity):
    """A representation of a OS Default Template entity."""
    operatingsystem = orm.OneToOneField('OperatingSystem')
    template_kind = orm.OneToOneField('TemplateKind', null=True)
    config_template = orm.OneToOneField('ConfigTemplate', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Create a os default template for operating system
            '/api/v2/operatingsystems/:operatingsystem_id/'
            'os_default_templates',
        )


class OverrideValue(orm.Entity):
    """A representation of a Override Value entity."""
    smart_variable = orm.OneToOneField('SmartVariable')
    match = orm.StringField(null=True)
    value = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
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
        api_path = (
            # Create a nested parameter for host
            '/api/v2/hosts/:host_id/parameters',
            # Create a nested parameter for hostgroup
            '/api/v2/hostgroups/:hostgroup_id/parameters',
            # Create a nested parameter for domain
            '/api/v2/domains/:domain_id/parameters',
            # Create a nested parameter for operating system
            '/api/v2/operatingsystems/:operatingsystem_id/parameters',
            # Create a nested parameter for location
            '/api/v2/locations/:location_id/parameters',
            # Create a nested parameter for organization
            '/api/v2/organizations/:organization_id/parameters',
        )


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
        api_path = (
            # Create a roles permission
            '/katello/api/v2/roles/:role_id/permissions',
        )


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
        api_path = (
            '/katello/api/v2/products',  # Create a product
        )


class PartitionTable(orm.Entity):
    """A representation of a Partition Table entity."""
    name = orm.StringField(required=True)
    layout = orm.StringField(required=True)
    os_family = orm.StringField(null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/ptables',  # Create a ptable.
        )


class PuppetClass(orm.Entity):
    """A representation of a Puppet Class entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/puppetclasses',  # Create a puppetclass.
        )


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
        api_path = (
            '/api/v2/realms',  # Create a realm.
        )


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
        api_path = (
            '/api/v2/reports',  # Create a report.
        )


class Repository(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a Repository entity."""
    name = orm.StringField(required=True)
    label = orm.StringField()
    # Product the repository belongs to
    product = orm.OneToOneField('Product', required=True)
    # repository source url
    url = orm.StringField(required=True)
    # id of the gpg key that will be assigned to the new repository
    gpg_key = orm.OneToOneField('GPGKey')
    # true if this repository can be published via HTTP
    unprotected = orm.BooleanField()
    # type of repo (either 'yum' or 'puppet', defaults to 'yum')
    content_type = orm.StringField(default='yum', required=True)
    #choices=('puppet', 'yum'),
    url = orm.StringField(
        default=(
            'http://inecas.fedorapeople.org/' +
            'fakerepos/new_cds/content/zoo/1.1/x86_64/rpms/'
        ),
        required=True
    )

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/repositories',  # Create a custom repository
        )


class RoleLDAPGroups(orm.Entity):
    """A representation of a Role LDAP Groups entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Add group to list of LDAP groups associated with the role
            '/katello/api/v2/roles/:role_id/ldap_groups',
        )


class Role(orm.Entity):
    """A representation of a Role entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/katello/api/v2/roles',  # Create an role.
        )


class SmartProxy(orm.Entity):
    """A representation of a Smart Proxy entity."""
    name = orm.StringField(required=True)
    url = orm.URLField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/smart_proxies',  # Create a Capsule.
        )


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
        api_path = (
            '/api/v2/smart_variables',  # Create a smart variable.
        )


class Subnet(orm.Entity, factory.EntityFactoryMixin):
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
        api_path = (
            '/api/v2/subnets',  # Create a subnet
        )


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
        api_path = (
            # Add a subscription to a resource
            '/katello/api/v2/subscriptions/:id',
            # Add a subscription to a system
            '/katello/api/v2/systems/:system_id/subscriptions',
            # Add a subscription to an activation key
            '/katello/api/v2/activation_keys/:activation_key_id/subscriptions',
        )


class SyncPlan(orm.Entity):
    """A representation of a Sync Plan entity."""
    organization = orm.OneToOneField('Organization', required=True)
    name = orm.StringField(required=True)
    # how often synchronization should run must be one of: none, hourly, daily,
    # weekly.
    interval = orm.StringField(
        choices=('none', 'hourly', 'daily', 'weekly'), required=True)
    # start datetime of synchronization
    sync_date = orm.DateTimeField(required=True)
    description = orm.StringField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Create a sync plan
            '/katello/api/v2/organizations/:organization_id/sync_plans',
        )


class SystemPackage(orm.Entity):
    """A representation of a System Package entity."""
    system = orm.OneToOneField('System', required=True)
    # List of package names
    packages = orm.ListField()
    # List of package group names
    groups = orm.ListField()

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Install packages remotely
            '/katello/api/v2/systems/:system_id/packages',
        )


class System(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a System entity."""
    name = orm.StringField(style='alpha', required=True)
    description = orm.StringField()
    # Physical location of the content host
    location = orm.StringField()
    # Any number of facts about this content host
    facts = orm.StringField(
        default={"uname.machine": "unknown"},
        required=True
    )
    # Type of the content host, it should always be 'content host'
    system_type = orm.StringField(default='system', required=True)
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
    environment_id = orm.StringField(default='1', required=True)
    content_view_id = orm.StringField(default='1', required=True)
    organization = orm.OneToOneField('Organization', required=True)
    host_collection = orm.OneToOneField('HostCollection')

    class Meta(object):
        """Non-field information about this entity."""
        api_names = (('system_type', 'type'),)
        api_path = (
            # Register a content host
            '/katello/api/v2/systems',
            # Register a content host in environment
            '/katello/api/v2/environments/:environment_id/systems',
            # Register a content host in environment
            '/katello/api/v2/host_collections/:host_collection_id/systems',
        )


class TemplateCombination(orm.Entity):
    """A representation of a Template Combination entity."""
    config_template = orm.OneToOneField('ConfigTemplate', required=True)
    environment = orm.OneToOneField('Environment', null=True)
    hostgroup = orm.OneToOneField('HostGroup', null=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            # Add a Template Combination
            '/api/v2/config_templates/:config_template_id/'
            'template_combinations',
        )


class TemplateKind(orm.Entity):
    """A representatio of a Template Kind entity."""
    # FIXME figure out fields


class UserGroup(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a User Group entity."""
    name = orm.StringField(required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/usergroups',  # Create a usergroup.
        )


class User(orm.Entity, factory.EntityFactoryMixin):
    """A representation of a User entity."""
    login = orm.StringField(style='alpha', required=True)
    firstname = orm.StringField(null=True)
    lastname = orm.StringField(null=True)
    mail = orm.EmailField(required=True)
    # Is an admin account?
    admin = orm.BooleanField(null=True)
    password = orm.StringField(style='alphanumeric', required=True)
    default_location = orm.OneToOneField('Location', null=True)
    default_organization = orm.OneToOneField('Organization', null=True)
    auth_source_id = orm.StringField(default='1', required=True)

    class Meta(object):
        """Non-field information about this entity."""
        api_path = (
            '/api/v2/users',  # Create an user.
        )

    def _pack_request(self, request):
        return {"user": request}
