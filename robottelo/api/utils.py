# -*- encoding: utf-8 -*-
"""Module containing convenience functions for working with the API."""
import time

from inflector import Inflector
from nailgun import entities
from robottelo import ssh
from robottelo.constants import PERMISSIONS_WITH_BZ
from robottelo.decorators import bz_bug_is_open


def enable_rhrepo_and_fetchid(basearch, org_id, product, repo,
                              reposet, releasever):
    """Enable a RedHat Repository and fetches it's Id.
    :param str org_id: The organization Id.
    :param str product: The product name in which repository exists.
    :param str reposet: The reposet name in which repository exists.
    :param str repo: The repository name who's Id is to be fetched.
    :param str basearch: The architecture of the repository.
    :param str releasever: The releasever of the repository.
    :return: Returns the repository Id.
    :rtype: str

    """
    product = entities.Product(name=product, organization=org_id).search()[0]
    r_set = entities.RepositorySet(name=reposet, product=product).search()[0]
    payload = {}
    if basearch is not None:
        payload['basearch'] = basearch
    if releasever is not None:
        payload['releasever'] = releasever
    r_set.enable(data=payload)
    result = entities.Repository(name=repo).search(
        query={'organization_id': org_id})
    if bz_bug_is_open(1252101):
        for _ in range(5):
            if len(result) > 0:
                break
            time.sleep(5)
            result = entities.Repository(name=repo).search(
                query={'organization_id': org_id})
    return result[0].id


def promote(content_view_version, environment_id, force=False):
    """Call ``content_view_version.promote(…)``.

    :param content_view_version: A ``nailgun.entities.ContentViewVersion``
        object.
    :param environment_id: An environment ID.
    :param force: Whether to force the promotion or not. Only needed if
        promoting to a lifecycle environment that is not the next in order
        of sequence.
    :returns: Whatever ``nailgun.entities.ContentViewVersion.promote`` returns.

    """
    data = {
        u'environment_id': environment_id,
        u'force': True if force else False,
    }
    return content_view_version.promote(data=data)


def upload_manifest(organization_id, manifest):
    """Call ``nailgun.entities.Subscription.upload``.

    :param organization_id: An organization ID.
    :param manifest: A file object referencing a Red Hat Satellite 6 manifest.
    :returns: Whatever ``nailgun.entities.Subscription.upload`` returns.

    """
    return entities.Subscription().upload(
        data={'organization_id': organization_id},
        files={'content': manifest},
    )


def publish_puppet_module(puppet_modules, repo_url, organization_id=None):
    """Creates puppet repo, sync it via provided url and publish using
    Content View publishing mechanism. It makes puppet class available
    via Puppet Environment created by Content View and returns Content
    View entity.

    :param puppet_modules: List of dictionaries with module 'author' and
        module 'name' fields.
    :param str repo_url: Url of the repo that can be synced using pulp:
        pulp repo or puppet forge.
    :param organization_id: Organization id that is shared between
        created entities.
    :return: `nailgun.entities.ContentView` entity.
    """
    if not organization_id:
        organization_id = entities.Organization().create().id
    # Create product and puppet modules repository
    product = entities.Product(organization=organization_id).create()
    repo = entities.Repository(
        product=product,
        content_type='puppet',
        url=repo_url
    ).create()
    # Synchronize repo via provided URL
    repo.sync()
    # Add selected module to Content View
    cv = entities.ContentView(organization=organization_id).create()
    for module in puppet_modules:
        entities.ContentViewPuppetModule(
            author=module['author'],
            name=module['name'],
            content_view=cv,
        ).create()
    # CV publishing will automatically create Environment and
    # Puppet Class entities
    cv.publish()
    return cv.read()


def delete_puppet_class(puppetclass_name, puppet_module=None,
                        proxy_hostname=None, environment_name=None):
    """Removes puppet class entity and uninstall puppet module from Capsule if
    puppet module name and Capsule details provided.

    :param str puppetclass_name: Name of the puppet class entity that should be
        removed.
    :param str puppet_module: Name of the module that should be
        uninstalled via puppet.
    :param str proxy_hostname: Hostname of the Capsule from which puppet module
        should be removed.
    :param str environment_name: Name of environment where puppet module was
        imported.
    """
    # Find puppet class
    puppet_classes = entities.PuppetClass().search(
        query={'search': 'name = "{0}"'.format(puppetclass_name)}
    )
    # And all subclasses
    puppet_classes.extend(entities.PuppetClass().search(
        query={'search': 'name ~ "{0}::"'.format(puppetclass_name)})
    )
    for puppet_class in puppet_classes:
        # Search and remove puppet class from affected hostgroups
        for hostgroup in puppet_class.read().hostgroup:
            hostgroup.delete_puppetclass(
                data={'puppetclass_id': puppet_class.id}
            )
        # Search and remove puppet class from affected hosts
        for host in entities.Host().search(
                query={'search': 'class={0}'.format(puppet_class.name)}):
            host.delete_puppetclass(
                data={'puppetclass_id': puppet_class.id}
            )
        # Remove puppet class entity
        puppet_class.delete()
    # And remove puppet module from the system if puppet_module name provided
    if puppet_module and proxy_hostname and environment_name:
        ssh.command(
            'puppet module uninstall --force {0}'.format(puppet_module))
        env = entities.Environment().search(
            query={'search': 'name="{0}"'.format(environment_name)}
        )[0]
        proxy = entities.SmartProxy(name=proxy_hostname).search()[0]
        proxy.import_puppetclasses(environment=env)


def one_to_one_names(name):
    """Generate the names Satellite might use for a one to one field.

    Example of usage::

        >>> one_to_many_names('person') == {'person_name', 'person_id'}
        True

    :param name: A field name.
    :returns: A set including both ``name`` and variations on ``name``.

    """
    return set((name + '_name', name + '_id'))


def one_to_many_names(name):
    """Generate the names Satellite might use for a one to many field.

    Example of usage::

        >>> one_to_many_names('person') == {'person', 'person_ids', 'people'}
        True

    :param name: A field name.
    :returns: A set including both ``name`` and variations on ``name``.

    """
    return set((name, name + '_ids', Inflector().pluralize(name)))


def get_role_by_bz(bz_id):
    """Create and configure custom role entity for the testing of specific bugs
     This function will read the dictionary of permissions and their associated
     bugzilla id's from robottelo.constants "PERMISSIONS_WITH_BZ",
     these permissions will create filter and a single role will be created
     from all the filters.

     :param bz_id: This is the bugzilla id that is specified in the
        PERMISSIONS_WITH_BZ list, all the permissions associated with the bz_id
        will be fetched and filters will be created
     :return: A single role entity will be created from all the created filters
     """
    role = entities.Role().create()
    for perms in PERMISSIONS_WITH_BZ.values():
        perms_with_bz = [x for x in perms if bz_id in x.get('bz', [])]
        if perms_with_bz:
            permissions = [
                entities.Permission(name=perm['name']).search()[0]
                for perm in perms_with_bz
                ]
            entities.Filter(permission=permissions, role=role).create()
    return role.read()


def create_role_permissions(role, permissions_types_names):  # pragma: no cover
    """Create role permissions found in dict permissions_types_names.

    :param role: nailgun.entities.Role
    :param permissions_types_names: a dict containing resource types
        and permission names to add to the role, example usage.

          ::

           permissions_types_names = {
               None: ['access_dashboard'],
               'Organization': ['view_organizations'],
               'Location': ['view_locations'],
               'Katello::KTEnvironment': [
                   'view_lifecycle_environments',
                   'edit_lifecycle_environments',
                   'promote_or_remove_content_views_to_environments'
               ]
           }
           role = entities.Role(name='example_role_name').create()
           create_role_permissions(role, permissions_types_names)
    """
    for resource_type, permissions_name in permissions_types_names.items():
        if resource_type is None:
            permissions_entities = []
            for name in permissions_name:
                result = entities.Permission(name=name).search()
                if not result:
                    raise entities.APIResponseError(
                        'permission "{}" not found'.format(name))
                if len(result) > 1:
                    raise entities.APIResponseError(
                        'found more than one entity for permission'
                        ' "{}"'.format(name)
                    )
                entity_permission = result[0]
                if entity_permission.name != name:
                    raise entities.APIResponseError(
                        'the returned permission is different from the'
                        ' requested one "{0} != {1}"'.format(
                            entity_permission.name, name)
                    )
                permissions_entities.append(entity_permission)
        else:
            if not permissions_name:
                raise ValueError('resource type "{}" empty. You must select at'
                                 ' least one permission'.format(resource_type))

            resource_type_permissions_entities = entities.Permission(
                resource_type=resource_type).search()
            if not resource_type_permissions_entities:
                raise entities.APIResponseError(
                    'resource type "{}" permissions not found'.format(
                        resource_type)
                )

            permissions_entities = [
                entity
                for entity in resource_type_permissions_entities
                if entity.name in permissions_name
            ]
            # ensure that all the requested permissions entities where
            # retrieved
            permissions_entities_names = {
                entity.name for entity in permissions_entities
            }
            not_found_names = set(permissions_name).difference(
                permissions_entities_names)
            if not_found_names:
                raise entities.APIResponseError(
                    'permissions names entities not found'
                    ' "{}"'.format(not_found_names)
                )
        entities.Filter(
            permission=permissions_entities,
            role=role,
            search=None
        ).create()
