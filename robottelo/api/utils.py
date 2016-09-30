# -*- encoding: utf-8 -*-
"""Module containing convenience functions for working with the API."""
import time

from inflector import Inflector
from nailgun import entities
from robottelo import ssh
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
    puppet_class = entities.PuppetClass().search(
        query={'search': 'name="{0}"'.format(puppetclass_name)}
    )[0]
    # Search and remove puppet class from affected hostgroups
    for hostgroup in puppet_class.read().hostgroup:
        hostgroup.delete_puppetclass(data={'puppetclass_id': puppet_class.id})
    # Search and remove puppet class from affected hosts
    for host in entities.Host().search(
            query={'search': 'class={0}'.format(puppet_class.name)}):
        host.delete_puppetclass(data={'puppetclass_id': puppet_class.id})
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
