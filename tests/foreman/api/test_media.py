"""Tests for the ``media`` paths.

:Requirement: Media

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from fauxfactory import gen_string
from fauxfactory import gen_url
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.constants import OPERATING_SYSTEMS
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import APITestCase


class MediaTestCase(APITestCase):
    """Tests for ``api/v2/media``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(MediaTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create media with valid name only

        :id: 892b44d5-0f11-4e9d-8ee9-fd5abe0b0a9b

        :expectedresults: Media entity is created and has proper name

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                media = entities.Media(
                    organization=[self.org],
                    name=name,
                ).create()
                self.assertEqual(media.name, name)

    @tier1
    def test_positive_create_with_os_family(self):
        """Create media with every OS family possible

        :id: 7885e205-6189-4e71-a6ee-e5ddb077ecee

        :expectedresults: Media entity is created and has proper OS family
            assigned
        """
        for os_family in OPERATING_SYSTEMS:
            with self.subTest(os_family):
                media = entities.Media(
                    organization=[self.org],
                    os_family=os_family,
                ).create()
                self.assertEqual(media.os_family, os_family)

    @tier2
    def test_positive_create_with_location(self):
        """Create media entity assigned to non-default location

        :id: 1c4fa736-c145-46ca-9feb-c4046fc778c6

        :expectedresults: Media entity is created and has proper location

        :CaseLevel: Integration
        """
        location = entities.Location().create()
        media = entities.Media(
            organization=[self.org],
            location=[location],
        ).create()
        self.assertEqual(media.location[0].read().name, location.name)

    @tier2
    def test_positive_create_with_os(self):
        """Create media entity assigned to operation system entity

        :id: dec22198-ed07-480c-9306-fa5458baec0b

        :expectedresults: Media entity is created and assigned to expected OS

        :CaseLevel: Integration
        """
        os = entities.OperatingSystem().create()
        media = entities.Media(
            organization=[self.org],
            operatingsystem=[os],
        ).create()
        self.assertEqual(os.read().medium[0].read().name, media.name)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create media entity providing an invalid name

        :id: 0934f4dc-f674-40fe-a639-035761139c83

        :expectedresults: Media entity is not created

        :CaseImportance: Medium
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Media(name=name).create()

    @tier1
    def test_negative_create_with_invalid_url(self):
        """Try to create media entity providing an invalid URL

        :id: ae00b6bb-37ed-459e-b9f7-acc92ed0b262

        :expectedresults: Media entity is not created

        :CaseImportance: Medium
        """
        with self.assertRaises(HTTPError):
            entities.Media(path_='NON_EXISTENT_URL').create()

    @tier1
    def test_negative_create_with_invalid_os_family(self):
        """Try to create media entity providing an invalid OS family

        :id: 368b7eac-8c52-4071-89c0-1946d7101291

        :expectedresults: Media entity is not created

        :CaseImportance: Medium
        """
        with self.assertRaises(HTTPError):
            entities.Media(os_family='NON_EXISTENT_OS').create()

    @tier1
    def test_positive_update_name(self):
        """Create media entity providing the initial name, then update
        its name to another valid name.

        :id: a99c3c27-ad0a-474f-ad80-cb61022618a9

        :expectedresults: Media entity is created and updated properly
        """
        media = entities.Media(organization=[self.org]).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                media = entities.Media(
                    id=media.id, name=new_name).update(['name'])
                self.assertEqual(media.name, new_name)

    @tier2
    def test_positive_update_url(self):
        """Create media entity providing the initial url path, then
        update that url to another valid one.

        :id: 997fd9f6-4809-4de8-869d-7a4a0bf4c958

        :expectedresults: Media entity is created and updated properly

        :CaseImportance: Medium
        """
        media = entities.Media(organization=[self.org]).create()
        new_url = gen_url(subdomain=gen_string('alpha'))
        media = entities.Media(id=media.id, path_=new_url).update(['path_'])
        self.assertEqual(media.path_, new_url)

    @tier1
    def test_positive_update_os_family(self):
        """Create media entity providing the initial os family, then
        update that operation system to another valid one from the list.

        :id: 4daca3f4-39c9-43ec-92f2-a1e506147d71

        :expectedresults: Media entity is created and updated properly

        :CaseImportance: Medium
        """
        media = entities.Media(
            organization=[self.org],
            os_family=OPERATING_SYSTEMS[0],
        ).create()
        new_os_family = OPERATING_SYSTEMS[
            random.randint(1, len(OPERATING_SYSTEMS)-1)]
        media.os_family = new_os_family
        self.assertEqual(media.update(['os_family']).os_family, new_os_family)

    @tier1
    def test_negative_update_name(self):
        """Create media entity providing the initial name, then try to
        update its name to invalid one.

        :id: 1c7d3af1-8cef-454e-80b6-a8e95b5dfa8b

        :expectedresults: Media entity is not updated

        :CaseImportance: Medium
        """
        media = entities.Media(organization=[self.org]).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.Media(id=media.id, name=new_name).update(['name'])

    @tier1
    def test_negative_update_url(self):
        """Try to update media with invalid url.

        :id: 6832f178-4adc-4bb1-957d-0d8d4fd8d9cd

        :expectedresults: Media entity is not updated

        :CaseImportance: Medium
        """
        media = entities.Media(organization=[self.org]).create()
        with self.assertRaises(HTTPError):
            entities.Media(
                id=media.id, path_='NON_EXISTENT_URL').update(['path_'])

    @tier1
    def test_negative_update_os_family(self):
        """Try to update media with invalid operation system.

        :id: f4c5438d-5f98-40b1-9bc7-c0741e81303a

        :expectedresults: Media entity is not updated

        :CaseImportance: Medium
        """
        media = entities.Media(organization=[self.org]).create()
        with self.assertRaises(HTTPError):
            entities.Media(
                id=media.id, os_family='NON_EXISTENT_OS').update(['os_family'])

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create new media entity and then delete it.

        :id: 178c8ee2-2f69-41df-a604-e8a9e6c396ab

        :expectedresults: Media entity is deleted successfully

        :CaseImportance: High
        """
        for name in valid_data_list():
            with self.subTest(name):
                media = entities.Media(
                    organization=[self.org],
                    name=name,
                ).create()
                media.delete()
                with self.assertRaises(HTTPError):
                    media.read()
