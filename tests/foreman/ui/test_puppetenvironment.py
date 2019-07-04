# -*- encoding: utf-8 -*-
"""Test class for Environment UI

:Requirement: Environment

:CaseAutomation: notautomated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
import pytest
from robottelo.datafactory import (
    gen_string,
)


@pytest.fixture(scope='module')
def init_values():
    """Fixture returns values for new environment"""
    name = gen_string('alpha')
    org = entities.Organization().create()
    location = entities.Location().create()
    puppetEnvironmentValues = {
        'environment.name': name,
        'locations.resources.assigned': [location.name],
        'organizations.resources.assigned': [org.name],
    }
    return puppetEnvironmentValues
