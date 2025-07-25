"""Tests for the ``media`` paths.

:Requirement: Media

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

import random

from fauxfactory import gen_string, gen_url
import pytest
from requests.exceptions import HTTPError

from robottelo.constants import OPERATING_SYSTEMS
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
)


class TestMedia:
    """Tests for ``api/v2/media``."""

    @pytest.fixture(scope='class')
    def class_media(self, module_org, class_target_sat):
        return class_target_sat.api.Media(organization=[module_org]).create()

    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        ('name', 'new_name'),
        **parametrized(
            list(zip(valid_data_list().values(), valid_data_list().values(), strict=True))
        ),
    )
    def test_positive_crud_with_name(self, module_org, name, new_name, module_target_sat):
        """Create, update, delete media with valid name only

        :id: b07a4549-7dd5-4b36-a1b4-9f8d48ddfcb5

        :parametrized: yes

        :expectedresults: Media entity is created and has proper name

        :CaseImportance: Critical
        """
        media = module_target_sat.api.Media(organization=[module_org], name=name).create()
        assert media.name == name
        media = module_target_sat.api.Media(id=media.id, name=new_name).update(['name'])
        assert media.name == new_name
        media.delete()
        with pytest.raises(HTTPError):
            media.read()

    @pytest.mark.parametrize('os_family', **parametrized(OPERATING_SYSTEMS))
    def test_positive_create_update_with_os_family(self, module_org, os_family, module_target_sat):
        """Create and update media with every OS family possible

        :id: d02404f0-b2ad-412c-b1cd-0548254f7c88

        :parametrized: yes

        :expectedresults: Media entity is created and has proper OS family
            assigned
        """
        media = module_target_sat.api.Media(organization=[module_org], os_family=os_family).create()
        assert media.os_family == os_family
        new_os_family = new_os_family = random.choice(OPERATING_SYSTEMS)
        media.os_family = new_os_family
        assert media.update(['os_family']).os_family == new_os_family

    def test_positive_create_with_location(self, module_org, module_location, module_target_sat):
        """Create media entity assigned to non-default location

        :id: 1c4fa736-c145-46ca-9feb-c4046fc778c6

        :expectedresults: Media entity is created and has proper location

        """
        media = module_target_sat.api.Media(
            organization=[module_org], location=[module_location]
        ).create()
        assert media.location[0].read().name == module_location.name

    def test_positive_create_with_os(self, module_org, module_target_sat):
        """Create media entity assigned to operation system entity

        :id: dec22198-ed07-480c-9306-fa5458baec0b

        :expectedresults: Media entity is created and assigned to expected OS

        """
        os = module_target_sat.api.OperatingSystem().create()
        media = module_target_sat.api.Media(
            organization=[module_org], operatingsystem=[os]
        ).create()
        assert os.read().medium[0].read().name == media.name

    def test_positive_create_update_url(self, module_org, module_target_sat):
        """Create media entity providing the initial url path, then
        update that url to another valid one.

        :id: a183ee1f-1633-42cd-9132-cce451861b2a

        :expectedresults: Media entity is created and updated properly

        :CaseImportance: Medium
        """
        url = gen_url(subdomain=gen_string('alpha'))
        media = module_target_sat.api.Media(organization=[module_org], path_=url).create()
        assert media.path_ == url
        new_url = gen_url(subdomain=gen_string('alpha'))
        media = module_target_sat.api.Media(id=media.id, path_=new_url).update(['path_'])
        assert media.path_ == new_url

    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_invalid_name(self, name, target_sat):
        """Try to create media entity providing an invalid name

        :id: 0934f4dc-f674-40fe-a639-035761139c83

        :parametrized: yes

        :expectedresults: Media entity is not created

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError):
            target_sat.api.Media(name=name).create()

    def test_negative_create_with_invalid_url(self, target_sat):
        """Try to create media entity providing an invalid URL

        :id: ae00b6bb-37ed-459e-b9f7-acc92ed0b262

        :expectedresults: Media entity is not created

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError):
            target_sat.api.Media(path_='NON_EXISTENT_URL').create()

    def test_negative_create_with_invalid_os_family(self, target_sat):
        """Try to create media entity providing an invalid OS family

        :id: 368b7eac-8c52-4071-89c0-1946d7101291

        :expectedresults: Media entity is not created

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError):
            target_sat.api.Media(os_family='NON_EXISTENT_OS').create()

    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, class_media, new_name, target_sat):
        """Create media entity providing the initial name, then try to
        update its name to invalid one.

        :id: 1c7d3af1-8cef-454e-80b6-a8e95b5dfa8b

        :parametrized: yes

        :expectedresults: Media entity is not updated

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError):
            target_sat.api.Media(id=class_media.id, name=new_name).update(['name'])

    def test_negative_update_url(self, class_media, target_sat):
        """Try to update media with invalid url.

        :id: 6832f178-4adc-4bb1-957d-0d8d4fd8d9cd

        :expectedresults: Media entity is not updated

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError):
            target_sat.api.Media(id=class_media.id, path_='NON_EXISTENT_URL').update(['path_'])

    def test_negative_update_os_family(self, class_media, target_sat):
        """Try to update media with invalid operation system.

        :id: f4c5438d-5f98-40b1-9bc7-c0741e81303a

        :expectedresults: Media entity is not updated

        :CaseImportance: Medium
        """
        with pytest.raises(HTTPError):
            target_sat.api.Media(id=class_media.id, os_family='NON_EXISTENT_OS').update(
                ['os_family']
            )
