"""Test class for Puppet Classes CLI

:Requirement: Puppetclass

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_org
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.puppet import Puppet
from robottelo.config import settings
from robottelo.constants.repos import CUSTOM_PUPPET_REPO


@pytest.fixture(scope='module')
def make_puppet():
    """Import a parametrized puppet class."""
    puppet_modules = [{'author': 'robottelo', 'name': 'generic_1'}]
    org = make_org()
    cv = publish_puppet_module(puppet_modules, CUSTOM_PUPPET_REPO, org['id'])
    env = Environment.list({'search': f'content_view="{cv["name"]}"'})[0]
    puppet = Puppet.info({'name': puppet_modules[0]['name'], 'environment': env['name']})
    return puppet


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason="Missing repos_hosting_url")
def test_positive_list_smart_class_parameters(make_puppet):
    """List smart class parameters associated with the puppet class.

    :id: 56b370c2-8fc6-49be-9676-242178cc709a

    :expectedresults: Smart class parameters listed for the class.
    """
    class_sc_parameters = Puppet.sc_params({'puppet-class': make_puppet['name']})
    assert len(class_sc_parameters) == 200
