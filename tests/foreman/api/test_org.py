# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# pylint: disable=R0904

from ddt import ddt
from robottelo.api.apicrud import ApiCrud, ApiException
from robottelo.common.decorators import data, skip_if_bz_bug_open, stubbed
from robottelo.common.helpers import STR
from robottelo.common.records.base import NoEnum
from robottelo.common.records.fields import BasicPositiveField
from robottelo.records.organization import Organization
from robottelo.test import APITestCase


@ddt
class TestOrganization(APITestCase):
    """Testing /api/organization entrypoint"""

    # Positive Create

    @data(*Organization.enumerate(label="", description=""))
    def test_positive_create_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name only
        @assert: organization is created, label is auto-generated
        """
        result = ApiCrud.record_create(test_data)
        test_data.label = result.label
        self.assertIntersects(test_data, result)

    @data(*Organization.enumerate(name="", description=""))
    def test_positive_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid matching name and label only
        @assert: organization is created, label matches name
        """
        test_data.name = test_data.label
        result = ApiCrud.record_create(test_data)
        self.assertIntersects(test_data, result)
        self.assertEquals(result.name, result.label)

    @data(*Organization.enumerate(description=""))
    def test_positive_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid unmatching name and label only
        @assert: organization is created, label does not match name
        """
        result = ApiCrud.record_create(test_data)
        self.assertIntersects(test_data, result)
        self.assertNotEqual(result.name, result.label)

    @data(*Organization.enumerate(label=""))
    def test_positive_create_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name and description only
        @assert: organization is created, label is auto-generated
        """

        result = ApiCrud.record_create(test_data)
        test_data.label = result.label
        self.assertIntersects(test_data, result)

    @data(*Organization.enumerate())
    def test_positive_create_5(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name, label and description
        @assert: organization is created
        """
        result = ApiCrud.record_create(test_data)
        self.assertIntersects(test_data, result)

    # Negative Create

    @data(
        *Organization.enumerate(
            name=BasicPositiveField(maxlen=300),
            label=NoEnum,
            description=NoEnum)
    )
    def test_negative_create_0(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        too long
        @assert: organization is not created
        """
        correctly_failing = True
        try:
            ApiCrud.record_create(test_data)
            correctly_failing = False
        except ApiException:
            correctly_failing = True
        self.assertTrue(correctly_failing)

    @data(*Organization.enumerate(name=""))
    def test_negative_create_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        blank
        @assert: organization is not created
        """
        try:
            ApiCrud.record_create(test_data)
            correctly_failing = False
        except ApiException:
            correctly_failing = True

        self.assertTrue(correctly_failing)

    @data(*Organization.enumerate(name="   "))
    def test_negative_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        whitespace
        @assert: organization is not created
        """
        try:
            ApiCrud.record_create(test_data)
            correctly_failing = False
        except ApiException:
            correctly_failing = True
        self.assertTrue(correctly_failing)

    @data(*Organization.enumerate())
    def test_negative_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values, then create a new one
        with same values.
        @assert: organization is not created
        """
        ApiCrud.record_create(test_data)
        try:
            ApiCrud.record_create(test_data)
            correctly_failing = False
        except ApiException:
            correctly_failing = True
        self.assertTrue(correctly_failing)

    # Positive Delete

    @stubbed('Organization deletion is disabled')
    @skip_if_bz_bug_open('1061658')
    @data(*Organization.enumerate())
    def test_positive_delete_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then delete it
        @assert: organization is deleted
        """
        t = ApiCrud.record_create(test_data)
        self.assertTrue(ApiCrud.record_exists(t))
        ApiCrud.record_remove(t)
        self.assertFalse(ApiCrud.record_exists(t))

    # Negative Delete

    # Positive Update

    @data(*Organization.enumerate(
        label=NoEnum,
        description=NoEnum)
    )
    def test_positive_update_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its name
        @assert: organization name is updated
        """
        org = Organization()
        org = ApiCrud.record_create(org)
        org.name = test_data.name
        ApiCrud.record_update(org)

    @data(*Organization.enumerate(
        name=NoEnum,
        label=NoEnum)
    )
    def test_positive_update_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its
        description
        @assert: organization description is updated
        """
        org = Organization()
        org = ApiCrud.record_create(org)
        org.description = test_data.description
        ApiCrud.record_update(org)

    @skip_if_bz_bug_open('1061658')
    @data(*Organization.enumerate())
    def test_positive_update_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update all values
        @assert: organization name, label and description are updated
        """
        org = Organization()
        org = ApiCrud.record_create(org)
        org.name = test_data.name
        org.description = test_data.description

        ApiCrud.record_update(org)

    # Negative Update

    @data(*Organization.enumerate(
        name=BasicPositiveField(maxlen=300),
        label=NoEnum,
        description=NoEnum
        ))
    def test_negative_update_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its name
        @assert: organization name is not updated
        """
        org = Organization()
        org = ApiCrud.record_create(org)
        org.name = test_data.name
        correctly_failing = True
        try:
            ApiCrud.record_update(org)
            correctly_failing = False
        except ApiException:
            correctly_failing = correctly_failing and True

        self.assertTrue(correctly_failing)

    @data(*Organization.enumerate(
        name=NoEnum,
        label=BasicPositiveField(),
        description=NoEnum
    ))
    def test_negative_update_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its label
        @assert: organization label is not updated
        """
        org = Organization()
        org = ApiCrud.record_create(org)
        org.label = test_data.label
        correctly_failing = True
        try:
            ApiCrud.record_update(org)
            correctly_failing = False
        except ApiException:
            correctly_failing = correctly_failing and True
        self.assertTrue(correctly_failing)

    # Miscelaneous

    @data(*Organization.enumerate())
    def test_list_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization and list it
        @assert: organization is displayed/listed
        """
        org = ApiCrud.record_create(test_data)
        orgs = ApiCrud.record_list(org)
        self.assertTrue(any(org.name == ol.name for ol in orgs))

    @skip_if_bz_bug_open('1072905')
    @data(*Organization.enumerate())
    def test_search_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization and search/find it
        @assert: organization can be found
        @BZ: 1072905
        """

        ApiCrud.record_create(test_data)
        org_res = ApiCrud.record_resolve(test_data)
        self.assertEqual(org_res.name, test_data.name)

    @skip_if_bz_bug_open('1072905')
    @data(*Organization.enumerate(exclude=[STR.html]))
    def test_search_name_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization and search/find it
        @assert: organization can be found
        @BZ: 1072905
        """

        ApiCrud.record_create(test_data)
        query = {"search": "name=%s" % test_data.name}
        result = Organization._meta.api_class.list(json=query)
        self.assertTrue(result.ok)
        name = result.json()["results"][0]["name"]
        self.assertEqual(name, test_data.name)

    @data(*Organization.enumerate())
    def test_info_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create single organization and get its info
        @assert: specific information for organization matches the
        creation values
        """

        org = ApiCrud.record_create(test_data)
        org_res = ApiCrud.record_resolve(org)
        self.assertEqual(org_res.name, test_data.name)

    @stubbed
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @stubbed
    def test_remove_configtemplate_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove config template
        @assert: configtemplate is added then removed
        @status: manual
        """

        pass

    @stubbed
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @stubbed
    def test_add_configtemplate_1(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate name
        @assert: configtemplate is added
        @status: manual
        """

        pass

    @stubbed
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @stubbed
    def test_add_configtemplate_2(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization ID and
        configtemplate name
        @assert: configtemplate is added
        @status: manual
        """

        pass

    @stubbed
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @stubbed
    def test_add_configtemplate_3(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate ID
        @assert: configtemplate is added
        @status: manual
        """

        pass

    @stubbed
    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    @stubbed
    def test_add_configtemplate_4(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization ID and
        configtemplate ID
        @assert: configtemplate is added
        @status: manual
        """

        pass
