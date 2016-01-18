"""Tests for the ``media`` paths."""
import random
from fauxfactory import gen_string, gen_url
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import OPERATING_SYSTEMS
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import run_only_on, tier1, tier2
from robottelo.test import APITestCase


class MediaTestCase(APITestCase):
    """Tests for ``api/v2/media``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(MediaTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create media with valid name only

        @Feature: Media

        @Assert: Media entity is created and has proper name
        """
        for name in valid_data_list():
            with self.subTest(name):
                media = entities.Media(
                    organization=[self.org],
                    name=name,
                ).create()
                self.assertEqual(media.name, name)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_os_family(self):
        """Create media with every OS family possible

        @Feature: Media

        @Assert: Media entity is created and has proper OS family assigned
        """
        for os_family in OPERATING_SYSTEMS:
            with self.subTest(os_family):
                media = entities.Media(
                    organization=[self.org],
                    os_family=os_family,
                ).create()
                self.assertEqual(media.os_family, os_family)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_location(self):
        """Create media entity assigned to non-default location

        @Feature: Media

        @Assert: Media entity is created and has proper location
        """
        location = entities.Location().create()
        media = entities.Media(
            organization=[self.org],
            location=[location],
        ).create()
        self.assertEqual(media.location[0].read().name, location.name)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_os(self):
        """Create media entity assigned to operation system entity

        @Feature: Media

        @Assert: Media entity is created and assigned to expected OS
        """
        os = entities.OperatingSystem().create()
        media = entities.Media(
            organization=[self.org],
            operatingsystem=[os],
        ).create()
        self.assertEqual(os.read().medium[0].read().name, media.name)

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_invalid_name(self):
        """Try to create media entity providing an invalid name

        @Feature: Media

        @Assert: Media entity is not created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Media(name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_invalid_url(self):
        """Try to create media entity providing an invalid URL

        @Feature: Media

        @Assert: Media entity is not created
        """
        with self.assertRaises(HTTPError):
            entities.Media(path_='NON_EXISTENT_URL').create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_invalid_os_family(self):
        """Try to create media entity providing an invalid OS family

        @Feature: Media

        @Assert: Media entity is not created
        """
        with self.assertRaises(HTTPError):
            entities.Media(os_family='NON_EXISTENT_OS').create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Create media entity providing the initial name, then update
        its name to another valid name.

        @Feature: Media

        @Assert: Media entity is created and updated properly
        """
        media = entities.Media(organization=[self.org]).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                media = entities.Media(
                    id=media.id, name=new_name).update(['name'])
                self.assertEqual(media.name, new_name)

    @tier2
    @run_only_on('sat')
    def test_positive_update_url(self):
        """Create media entity providing the initial url path, then
        update that url to another valid one.

        @Feature: Media

        @Assert: Media entity is created and updated properly
        """
        media = entities.Media(organization=[self.org]).create()
        new_url = gen_url(subdomain=gen_string('alpha'))
        media = entities.Media(id=media.id, path_=new_url).update(['path_'])
        self.assertEqual(media.path_, new_url)

    @tier1
    @run_only_on('sat')
    def test_positive_update_os_family(self):
        """Create media entity providing the initial os family, then
        update that operation system to another valid one from the list.

        @Feature: Media

        @Assert: Media entity is created and updated properly
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
    @run_only_on('sat')
    def test_negative_update_name(self):
        """Create media entity providing the initial name, then try to
        update its name to invalid one.

        @Feature: Media

        @Assert: Media entity is not updated
        """
        media = entities.Media(organization=[self.org]).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.Media(id=media.id, name=new_name).update(['name'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_url(self):
        """Try to update media with invalid url.

        @Feature: Media

        @Assert: Media entity is not updated
        """
        media = entities.Media(organization=[self.org]).create()
        with self.assertRaises(HTTPError):
            entities.Media(
                id=media.id, path_='NON_EXISTENT_URL').update(['path_'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_os_family(self):
        """Try to update media with invalid operation system.

        @Feature: Media

        @Assert: Media entity is not updated
        """
        media = entities.Media(organization=[self.org]).create()
        with self.assertRaises(HTTPError):
            entities.Media(
                id=media.id, os_family='NON_EXISTENT_OS').update(['os_family'])

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create new media entity and then delete it.

        @Feature: Media

        @Assert: Media entity is deleted successfully
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
