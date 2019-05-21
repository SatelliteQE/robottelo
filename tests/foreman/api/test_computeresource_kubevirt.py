# -*- encoding: utf-8 -*-
"""Unit tests for the ``compute_resource`` paths.

A full API reference for compute resources can be found here:
http://www.katello.org/docs/api/apidoc/compute_resources.html


:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import skip_if_not_set, tier1, tier2
from robottelo.test import APITestCase


class ComputeResourceTestCase(APITestCase):
    """Tests for ``katello/api/v2/compute_resources``."""

    @classmethod
    def setUpClass(cls):
        """Set up organization and location for tests."""
        super(ComputeResourceTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        cls.kubevirt_hostname = settings.compute_resources.kubevirt_hostname
        cls.kubevirt_port = settings.compute_resources.kubevirt_port
        cls.kubevirt_namespace = settings.compute_resources.kubevirt_namespace
        cls.kubevirt_token = settings.compute_resources.kubevirt_token

    @tier1
    def test_positive_create_with_name(self):
        for name in valid_data_list():
            with self.subTest(name):
                compresource = entities.KubeVirtComputeResource(
                    location=[self.loc],
                    name=name,
                    organization=[self.org],
                    url=self.current_libvirt_url,
                ).create()
                self.assertEqual(compresource.name, name)
