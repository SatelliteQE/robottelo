# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

:Requirement: Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture

PUPPET_MODULES = [
    {'author': 'robottelo', 'name': 'ui_test_variables'}]


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def content_view(module_org):
    return publish_puppet_module(
        PUPPET_MODULES, CUSTOM_PUPPET_REPO, module_org)


@fixture(scope='module')
def puppet_env(content_view):
    return entities.Environment().search(
        query={'search': u'content_view="{0}"'.format(content_view.name)})[0]


@fixture(scope='module')
def puppet_class(puppet_env):
    puppet_class_entity = entities.PuppetClass().search(query={
        'search': u'name = "{0}" and environment = "{1}"'.format(
            PUPPET_MODULES[0]['name'], puppet_env.name)})[0]
    # We need to have at least one variable created to unblock WebUI for Smart
    # Variable interface page
    if len(entities.SmartVariable(
            puppetclass=puppet_class_entity).search({'puppetclass'})) == 0:
        entities.SmartVariable(puppetclass=puppet_class_entity).create()
    return puppet_class_entity


@fixture(scope='module')
def puppet_subclasses(puppet_env):
    return entities.PuppetClass().search(query={
        'search': u'name ~ "{0}::" and environment = "{1}"'.format(
            PUPPET_MODULES[0]['name'], puppet_env.name)
         })


@fixture(scope='module')
def module_host(module_org, content_view, puppet_env, puppet_class):
    lce = entities.LifecycleEnvironment().search(
        query={
            'search': 'organization_id="{0}" and name="{1}"'.format(
                module_org.id, ENVIRONMENT)
        })[0]
    host = entities.Host(
        organization=module_org,
        content_facet_attributes={
            'content_view_id': content_view.id,
            'lifecycle_environment_id': lce.id,
        }).create()
    host.environment = puppet_env
    host.update(['environment'])
    host.add_puppetclass(data={'puppetclass_id': puppet_class.id})
    return host


@fixture(scope='module')
def domain(module_host):
    return entities.Domain(id=module_host.domain.id).read().name


def test_positive_create(session, puppet_class):
    """Creates a Smart Variable using different names.

    :steps: Creates a smart variable with valid name

    :expectedresults: The smart variable is created successfully.

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        sv_values = session.smartvariable.read(name)
        assert sv_values['variable']['key'] == name
