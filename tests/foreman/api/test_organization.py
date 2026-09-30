"""Unit tests for the ``organizations`` paths.

Each class tests a single URL. A full list of URLs to be tested can be found on your satellite:
http://<satellite-host>/apidoc/v2/organizations.html

:Requirement: Organization

:CaseAutomation: Automated

:CaseComponent: OrganizationsandLocations

:Team: Endeavour

:CaseImportance: High

"""

import http
import json
from random import randint
import tempfile
from urllib.parse import urljoin
import random

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import mldsa
from fauxfactory import gen_string
from nailgun import client
import pytest
from requests.exceptions import HTTPError

from robottelo.config import get_credentials, settings
from robottelo.constants import DEFAULT_ORG, ML_DSA_65, RSA, SHA256_WITH_RSA
from robottelo.utils.datafactory import (
    invalid_values_list,
    valid_org_names_list,
)
from robottelo.utils.issue_handlers import is_open


class TestOrganization:
    """Tests for the ``organizations`` path."""

    def test_positive_create(self, target_sat):
        """Create an organization using a 'text/plain' content-type.

        :id: 6f67a3f0-0c1d-498c-9a35-28207b0faec2

        :expectedresults: HTTP 415 is returned.

        :CaseImportance: Critical
        """
        organization = target_sat.api.Organization()
        organization.create_missing()
        response = client.post(
            organization.path(),
            organization.create_payload(),
            auth=get_credentials(),
            headers={'content-type': 'text/plain'},
            verify=False,
        )
        if is_open('SAT-20559'):
            assert response.status_code in [http.client.UNSUPPORTED_MEDIA_TYPE, 500]
        else:
            assert response.status_code == http.client.UNSUPPORTED_MEDIA_TYPE

    @pytest.mark.build_sanity
    def test_positive_create_with_name_and_description(self, target_sat):
        """Create an organization and provide a name and description.

        :id: afeea84b-61ca-40bf-bb16-476432919115

        :expectedresults: The organization has the provided attributes and an
            auto-generated label.

        :CaseImportance: Critical
        """
        name = random.choice(valid_org_names_list())
        org = target_sat.api.Organization(name=name, description=name).create()
        assert org.name == name
        assert org.description == name

        # Was a label auto-generated?
        assert hasattr(org, 'label')
        assert isinstance(org.label, str)
        assert len(org.label) > 0

    @pytest.mark.migration_candidate
    def test_negative_create_with_invalid_name(self, target_sat):
        """Create an org with an incorrect name.

        :id: 9c6a4b45-a98a-4d76-9865-92d992fa1a22

        :expectedresults: The organization cannot be created.
        """
        name = random.choice(invalid_values_list())
        with pytest.raises(HTTPError):
            target_sat.api.Organization(name=name).create()

    @pytest.mark.migration_candidate
    def test_negative_create_with_same_name(self, target_sat):
        """Create two organizations with identical names.

        :id: a0f5333c-cc83-403c-9bf7-08fb372909dc

        :expectedresults: The second organization cannot be created.

        :CaseImportance: Critical
        """
        name = target_sat.api.Organization().create().name
        with pytest.raises(HTTPError):
            target_sat.api.Organization(name=name).create()

    def test_negative_check_org_endpoint(self, module_sca_manifest_org):
        """Check manifest cert is not exposed in api endpoint

        :id: 24130e54-cd7a-41de-ac78-6e89aebabe30

        :expectedresults: no cert information in org api endpoint

        :customerscenario: true

        :bz: 1828549

        :CaseImportance: High
        """
        orgstring = json.dumps(module_sca_manifest_org.read_json())
        assert 'BEGIN CERTIFICATE' not in orgstring
        assert 'BEGIN RSA PRIVATE KEY' not in orgstring

    def test_positive_search(self, target_sat):
        """Create an organization, then search for it by name.

        :id: f6f1d839-21f2-4676-8683-9f899cbdec4c

        :expectedresults: Searching returns at least one result.

        :CaseImportance: High
        """
        org = target_sat.api.Organization().create()
        orgs = target_sat.api.Organization().search(query={'search': f'name="{org.name}"'})
        assert len(orgs) == 1
        assert orgs[0].id == org.id
        assert orgs[0].name == org.name

    def test_negative_create_with_wrong_path(self, target_sat):
        """Attempt to create an organization using foreman API path
        (``api/v2/organizations``)

        :id: 499ae5ef-b1e4-4fb8-967a-57d525e06326

        :BZ: 1241068

        :expectedresults: API returns 404 error with 'Route overridden by
            Katello' message

        :CaseImportance: Critical
        """
        org = target_sat.api.Organization()
        org._meta['api_path'] = 'api/v2/organizations'
        with pytest.raises(HTTPError) as err:
            org.create()
        assert err.value.response.status_code == 404
        assert 'use the /katello API endpoint instead' in err.value.response.text

    def test_default_org_id_check(self, target_sat):
        """test to check the default_organization id

        :id: df066396-a069-4e9e-b3c1-c6d34a755ec0

        :BZ: 1713269

        :expectedresults: The default_organization ID remain 1.

        :CaseImportance: Low
        """
        default_org_id = (
            target_sat.api.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0].id
        )
        assert default_org_id == 1


class TestOrganizationUpdate:
    """Tests for the ``organizations`` path."""

    @pytest.fixture
    def module_org(self, target_sat):
        """Create an organization."""
        return target_sat.api.Organization().create()

    @pytest.mark.migration_candidate
    def test_positive_update_name(self, module_org):
        """Update an organization's name with valid values.

        :id: 68f2ba13-2538-407c-9f33-2447fca28cd5

        :expectedresults: The organization's name is updated.

        :CaseImportance: High
        """
        name = random.choice(valid_org_names_list())
        module_org.name = name
        module_org = module_org.update(['name'])
        assert module_org.name == name

    @pytest.mark.migration_candidate
    def test_positive_update_description(self, module_org):
        """Update an organization's description with valid values.

        :id: bd223197-1021-467e-8714-c1a767ae89af

        :expectedresults: The organization's description is updated.

        :CaseImportance: Medium
        """
        desc = random.choice(valid_org_names_list())
        module_org.description = desc
        module_org = module_org.update(['description'])
        assert module_org.description == desc

    def test_positive_update_user(self, module_org, target_sat):
        """Update an organization, associate user with it.

        :id: 2c0c0061-5b4e-4007-9f54-b61d6e65ef58

        :expectedresults: User is associated with organization.

        """
        user = target_sat.api.User().create()
        module_org.user = [user]
        module_org = module_org.update(['user'])
        assert len(module_org.user) == 1
        assert module_org.user[0].id == user.id

    def test_positive_update_subnet(self, module_org, target_sat):
        """Update an organization, associate subnet with it.

        :id: 3aa0b9cb-37f7-4e7e-a6ec-c1b407225e54

        :expectedresults: Subnet is associated with organization.

        """
        subnet = target_sat.api.Subnet().create()
        module_org.subnet = [subnet]
        module_org = module_org.update(['subnet'])
        assert len(module_org.subnet) == 1
        assert module_org.subnet[0].id == subnet.id

    def test_positive_add_and_remove_hostgroup(self, target_sat):
        """Add a hostgroup to an organization and then remove it

        :id: 7eb1aca7-fd7b-404f-ab18-21be5052a11f

        :BZ: 1395229

        :expectedresults: Hostgroup is added to organization and then removed

        :CaseImportance: Medium
        """
        org = target_sat.api.Organization().create()
        hostgroup = target_sat.api.HostGroup().create()
        org.hostgroup = [hostgroup]
        org = org.update(['hostgroup'])
        assert len(org.hostgroup) == 1
        org.hostgroup = []
        org = org.update(['hostgroup'])
        assert len(org.hostgroup) == 0

    @pytest.mark.upgrade
    def test_positive_add_and_remove_smart_proxy(self, target_sat):
        """Add a smart proxy to an organization

        :id: e21de720-3fa2-429b-bd8e-b6a48a13146d

        :expectedresults: Smart proxy is successfully added to organization

        :BZ: 1395229

        """
        # Every Satellite has a built-in smart proxy, so let's find it
        smart_proxy = target_sat.api.SmartProxy().search(
            query={'search': f'url = {target_sat.url}:9090'}
        )
        # Check that proxy is found and unpack it from the list
        assert len(smart_proxy) > 0
        smart_proxy = smart_proxy[0]
        # By default, newly created organization uses built-in smart proxy,
        # so we need to remove it first
        org = target_sat.api.Organization().create()
        org.smart_proxy = []
        org = org.update(['smart_proxy'])
        # Verify smart proxy was actually removed
        assert len(org.smart_proxy) == 0

        # Add smart proxy to organization
        org.smart_proxy = [smart_proxy]
        org = org.update(['smart_proxy'])
        # Verify smart proxy was actually added
        assert len(org.smart_proxy) == 1
        assert org.smart_proxy[0].id == smart_proxy.id

        org.smart_proxy = []
        org = org.update(['smart_proxy'])
        # Verify smart proxy was actually removed
        assert len(org.smart_proxy) == 0

    @pytest.mark.parametrize('update_field', ['name', 'label'])
    def test_negative_update(self, module_org, update_field, target_sat):
        """Update an organization's attributes with invalid values.

        :id: b7152d0b-5ab0-4d68-bfdf-f3eabcb5fbc6

        :expectedresults: The organization's attributes are not updated.

        :CaseImportance: Critical

        :parametrized: yes

        :BZ: 1089996

        :CaseImportance: Medium
        """
        update_dict = {
            update_field: gen_string(str_type='utf8', length=256 if update_field == 'name' else 10)
        }
        with pytest.raises(HTTPError):
            target_sat.api.Organization(id=module_org.id, **update_dict).update([update_field])


def _cert_from_bundle(bundle):
    """Pull the certificate out of a "private key + certificate" download.

    The certificate is the second half; the first half is the private key and
    won't load as a certificate.
    """
    start = '-----BEGIN CERTIFICATE-----'
    assert start in bundle, 'download had no certificate in it'
    cert_pem = start + bundle.split(start, 1)[1]
    return x509.load_pem_x509_certificate(cert_pem.encode())


class TestOrganizationDebugCertificate:
    """Debug-certificate algorithm params (SAT-48622)."""

    def test_positive_download_debug_cert_default(self, function_sca_manifest_org):
        """Download with no algorithms -> get the default certificate.

        :id: 56375060-2e52-41e2-a999-e5c5ef7e4e6f

        :Verifies: SAT-48622

        :expectedresults: A certificate comes back using the default algorithm.

        :CaseImportance: High
        """
        bundle = function_sca_manifest_org.download_debug_certificate()
        cert = _cert_from_bundle(bundle)
        assert cert.signature_algorithm_oid.dotted_string == SHA256_WITH_RSA

    def test_positive_download_debug_cert_empty_lists(self, function_sca_manifest_org):
        """Empty algorithm lists behave the same as passing nothing.

        :id: cf02c729-2f78-43a4-a54a-9423663a15e1

        :Verifies: SAT-48622

        :expectedresults: The default certificate comes back.

        :CaseImportance: Medium
        """
        bundle = function_sca_manifest_org.download_debug_certificate(
            params={
                'key_algorithms[]': [],
                'signature_algorithms[]': [],
            }
        )
        cert = _cert_from_bundle(bundle)
        assert cert.signature_algorithm_oid.dotted_string == SHA256_WITH_RSA

    def test_positive_download_debug_cert_with_mldsa(self, function_sca_manifest_org):
        """Request a post-quantum (ML-DSA) key and get it back.

        :id: 7a9b032f-493f-4f24-9005-e48fe846c87d

        :Verifies: SAT-48622

        :expectedresults: The certificate uses the requested ML-DSA algorithm.

        :CaseImportance: High
        """
        bundle = function_sca_manifest_org.download_debug_certificate(
            params={'key_algorithms[]': [ML_DSA_65]}
        )
        cert = _cert_from_bundle(bundle)
        assert isinstance(cert.public_key(), mldsa.MLDSA65PublicKey)

    @pytest.mark.parametrize(
        ('key_algorithm', 'signature_algorithm'),
        [(RSA, SHA256_WITH_RSA), (ML_DSA_65, SHA256_WITH_RSA)],
        ids=['rsa', 'mldsa'],
    )
    def test_positive_download_debug_cert_with_oids(
        self, function_sca_manifest_org, key_algorithm, signature_algorithm
    ):
        """Request specific algorithms by OID and get them back.

        :id: 15b8f97f-ff00-4fad-87f6-3a6471e1ee00

        :parametrized: yes

        :Verifies: SAT-48622

        :expectedresults: The certificate matches the requested signature OID.

        :CaseImportance: High
        """
        bundle = function_sca_manifest_org.download_debug_certificate(
            params={
                'key_algorithms[]': [key_algorithm],
                'signature_algorithms[]': [signature_algorithm],
            }
        )
        cert = _cert_from_bundle(bundle)
        assert cert.signature_algorithm_oid.dotted_string == signature_algorithm

    def test_negative_download_debug_cert_unsupported_algorithm(self, function_sca_manifest_org):
        """An algorithm Candlepin can't do -> HTTP 409.

        :id: db7b8c67-8fb8-486e-ab22-eb05d4e60bda

        :Verifies: SAT-48622

        :expectedresults: The API returns 409, not a 500 crash.

        :CaseImportance: High
        """
        with pytest.raises(HTTPError) as error:
            function_sca_manifest_org.download_debug_certificate(
                # TODO: use a real OID that Candlepin rejects (confirm on the box).
                params={'key_algorithms[]': ['1.2.3.4.5.6.7.8.9']}
            )
        assert error.value.response.status_code == 409

    def test_negative_download_debug_cert_invalid_oid(self, function_sca_manifest_org):
        """A garbage OID string is rejected.

        :id: 4c7623b1-b6af-49a6-ac8c-251bc45c7c52

        :Verifies: SAT-48622

        :expectedresults: The API returns a 4xx client error.

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError) as error:
            function_sca_manifest_org.download_debug_certificate(
                params={'key_algorithms[]': ['not-an-oid']}
            )
        # TODO: confirm the exact status on the box (409 is only for unsupported;
        # a malformed value may be 400 or 422).
        assert error.value.response.status_code in (400, 409, 422)

    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            {'yum': {'content_type': 'yum', 'unprotected': False, 'url': settings.repos.yum_2.url}}
        ),
        indirect=True,
    )
    def test_positive_pqc_cert_accesses_protected_repo(
        self, function_sca_manifest_org, repo, target_sat
    ):
        """A cert made with specific algorithms can still unlock a protected repo.

        Proves the certificate actually works, not just that it parses.
        Based on test_repository.py::test_positive_access_protected_repository.

        :id: db55c4fe-b135-4f3d-aa4c-0481e99c1739

        :parametrized: yes

        :Verifies: SAT-48622

        :expectedresults: Repo access is blocked (403) without the cert and
            allowed (200) with it.

        :CaseImportance: High
        """
        repo.sync()
        repo_url = urljoin(repo.full_path, 'repodata/repomd.xml')
        assert repo_url.startswith(target_sat.url)

        # No cert -> blocked.
        assert client.get(repo_url, verify=False).status_code == 403

        # Download a cert asking for ML-DSA, save it, use it.
        bundle = function_sca_manifest_org.download_debug_certificate(
            params={'key_algorithms[]': [ML_DSA_65], 'signature_algorithms[]': [SHA256_WITH_RSA]}
        )
        cert_path = f'{tempfile.gettempdir()}/{function_sca_manifest_org.label}.pem'
        with open(cert_path, 'w') as cert_file:
            cert_file.write(bundle)
        assert client.get(repo_url, cert=cert_path, verify=False).status_code == 200
