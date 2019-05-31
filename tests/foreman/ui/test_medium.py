# -*- encoding: utf-8 -*-
"""Test class for Medium UI

:Requirement: Medium

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities
from fauxfactory import gen_string, gen_url
from robottelo.constants import INSTALL_MEDIUM_URL
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_media, set_context
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class MediumTestCase(UITestCase):
    """Implements all Installation Media tests"""

    @tier1
    def test_positive_create(self):
        """Create a new media

        :id: 17067a4d-a639-4187-a51b-1eae825e4f9c

        :expectedresults: Media is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    path = INSTALL_MEDIUM_URL % gen_string('alpha', 6)
                    make_media(
                        session, name=name, path=path, os_family='Red Hat')
                    self.assertIsNotNone(self.medium.search(name))

    @tier1
    def test_negative_create_with_too_long_name(self):
        """Create a new install media with 256 characters in name

        :id: a15307a3-5a1f-4cca-8594-44e8f3295a51

        :expectedresults: Media is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 256)
        path = INSTALL_MEDIUM_URL % name
        with Session(self) as session:
            make_media(session, name=name, path=path, os_family='Red Hat')
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['name_haserror']))
            self.assertIsNone(self.medium.search(name))

    @tier1
    def test_negative_create_with_blank_name(self):
        """Create a new install media with blank and whitespace in name

        :id: db7a58dd-8f4a-4443-be17-e5029e1c2b0e

        :expectedresults: Media is not created

        :CaseImportance: Critical
        """
        path = INSTALL_MEDIUM_URL % gen_string('alpha', 6)
        with Session(self) as session:
            for name in '', '  ':
                with self.subTest(name):
                    make_media(
                        session, name=name, path=path, os_family='Red Hat')
                    self.assertIsNotNone(
                        self.medium.wait_until_element(
                            common_locators['name_haserror'])
                    )

    @tier1
    def test_negative_create_with_same_name(self):
        """Create a new install media with same name

        :id: 6379b9b4-a67e-4abf-b8b5-930e40b6c293

        :expectedresults: Media is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 6)
        path = INSTALL_MEDIUM_URL % name
        os_family = 'Red Hat'
        with Session(self) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['name_haserror']))

    @tier1
    def test_negative_create_without_path(self):
        """Create a new install media without media URL

        :id: 8ccdd659-3c11-4266-848f-919f3ac853be

        :expectedresults: Media is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 6)
        with Session(self) as session:
            make_media(session, name=name, path='', os_family='Red Hat')
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.medium.search(name))

    @tier1
    def test_negative_create_medium_with_same_path(self):
        """Create an install media with an existing URL

        :id: ce3367ef-5ad3-4d81-8174-fe5ba4eecb00

        :expectedresults: Media is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 6)
        new_name = gen_string('alpha', 6)
        path = INSTALL_MEDIUM_URL % gen_string('alpha', 6)
        os_family = 'Red Hat'
        with Session(self) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            make_media(session, name=new_name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.medium.search(new_name))

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete a media

        :id: 08c982ef-e8de-4d50-97f5-b8803d7eb9ca

        :expectedresults: Media is deleted

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 6)
        path = INSTALL_MEDIUM_URL % name
        with Session(self) as session:
            make_media(session, name=name, path=path, os_family='Red Hat')
            self.medium.delete(name)

    @tier1
    def test_positive_update(self):
        """Updates Install media with name, path, OS family

        :id: 6926eaec-fe74-4171-bc8e-76e28926456b

        :expectedresults: Media is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 6)
        newname = gen_string('alpha', 4)
        path = INSTALL_MEDIUM_URL % name
        newpath = INSTALL_MEDIUM_URL % newname
        with Session(self) as session:
            make_media(session, name=name, path=path, os_family='Red Hat')
            self.assertIsNotNone(self.medium.search(name))
            self.medium.update(name, newname, newpath, 'Debian')
            self.assertTrue(self, self.medium.search(newname))

    @tier1
    def test_positive_sort_by_url(self):
        """Create some medium entities and sort them by url path

        :id: 6399f4ad-c081-46c4-89f6-70e552fb603a

        :customerscenario: true

        :expectedresults: Medium entities are sorted properly

        :CaseImportance: Medium
        """
        organization = entities.Organization().create()
        path_list = [
            gen_url(subdomain=gen_string('alpha', 20).lower(), scheme='https')
            for _ in range(5)
        ]
        for url in path_list:
            entities.Media(path_=url, organization=[organization]).create()
        path_list.sort(key=lambda x: x.split('.', 1)[0], reverse=True)
        with Session(self) as session:
            set_context(session, org=organization.name)
            self.medium.navigate_to_entity()
            self.assertEqual(
                self.medium.sort_table_by_column('Path'),
                path_list[::-1]
            )
            self.assertEqual(
                self.medium.sort_table_by_column('Path'),
                path_list
            )
