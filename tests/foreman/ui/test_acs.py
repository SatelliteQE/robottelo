"""Tests for Alternate Content Sources UI

:Requirement: AlternateContentSources

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: AlternateContentSources

:Team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import CONTENT_CREDENTIALS_TYPES
from robottelo.constants import REPO_TYPE
from robottelo.utils.datafactory import gen_string


ssl_name, product_name, product_label, product_description = (gen_string('alpha') for _ in range(4))
repos_to_enable = ['rhae2.9_el8']


@pytest.fixture(scope='function')
def ui_acs_setup(session, target_sat, module_sca_manifest_org):
    """
    This fixture creates all the necessary data for the test to run.
    It creates an organization, content credentials, product and repositories.
    """

    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_sca_manifest_org.name)

        session.contentcredential.create(
            {
                'name': ssl_name,
                'content_type': CONTENT_CREDENTIALS_TYPES['ssl'],
                'content': gen_string('alpha'),
            }
        )

        session.product.create(
            {'name': product_name, 'label': product_label, 'description': product_description}
        )

        session.repository.create(
            product_name,
            {
                'name': gen_string('alpha'),
                'repo_type': REPO_TYPE['file'],
                'repo_content.upstream_url': settings.repos.file_type_repo.url,
            },
        )

        for repo in repos_to_enable:
            session.redhatrepository.enable(
                custom_query=constants.REPOS[repo]['id'],
                arch=constants.DEFAULT_ARCHITECTURE,
                entity_name=None,
            )

        return target_sat, module_sca_manifest_org


@pytest.mark.e2e
def test_acs_positive_end_to_end(session, ui_acs_setup):
    """
    Create, update, delete and refresh ACSes of all supported types.

    :id: 047452cc-5a9f-4473-96b1-d5b6830b7d6b

    :steps:
        1. Select an organization
        2. Create ACSes (all supported types/combinations)
        3. Create ACS on which deletion is going to be tested
        4. Test deletion
        5. Test refresh
        6. Test renaming and changing description
        7. Test editing capsules
        8. Test editing urls and subpaths
        9. Test editing credentials
        10. Test editing products


    :expectedresults:
        This test should create all supported types (10)
        of the Aleternate Content Sources one by one and asserts that actions
        were made correctly on them.
    """

    target_sat, module_sca_manifest_org = ui_acs_setup

    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_sca_manifest_org.name)

        # Create ACS using "Simplified" option with content type of "File"
        session.acs.create_new_acs(
            simplified_type=True,
            content_type='file',
            name='simpleFile',
            description='simpleFileDesc',
            add_all_capsules=True,
            use_http_proxies=True,
            products_to_add=product_name,
        )

        # Create ACS using "Simplified" option with content type of "Yum"
        session.acs.create_new_acs(
            simplified_type=True,
            content_type='yum',
            name='simpleYum',
            description='simpleYumDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            products_to_add=[constants.REPOS[repo]['product'] for repo in repos_to_enable],
        )

        # Create ACS using "Custom" option with content type of "File"
        # and using manual authentication
        session.acs.create_new_acs(
            custom_type=True,
            content_type='file',
            name='customFileManualAuth',
            description='customFileManualAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            subpaths=['test/'],
            manual_auth=True,
            username='test',
            password='test',
            verify_ssl=True,
            ca_cert=ssl_name,
        )

        # Create ACS using "Custom" option with content type of "Yum"
        # and using manual authentication
        session.acs.create_new_acs(
            custom_type=True,
            content_type='yum',
            name='customYumManualAuth',
            description='customYumManualAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            subpaths=['test/'],
            manual_auth=True,
            username='test',
            password='test',
            verify_ssl=True,
            ca_cert=ssl_name,
        )

        # Create ACS using "Custom" option with content type of "Yum"
        # and using content credentials authentication
        session.acs.create_new_acs(
            custom_type=True,
            content_type='yum',
            name='customYumContentAuth',
            description='customYumContentAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            subpaths=['test/'],
            content_credentials_auth=True,
            ssl_client_cert=ssl_name,
            ssl_client_key=ssl_name,
            verify_ssl=True,
            ca_cert=ssl_name,
        )

        # Create ACS using "Custom" option with content type of "File"
        # and using content credentials authentication
        session.acs.create_new_acs(
            custom_type=True,
            content_type='file',
            name='customFileContentAuth',
            description='customFileContentAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            subpaths=['test/'],
            content_credentials_auth=True,
            ssl_client_cert=ssl_name,
            ssl_client_key=ssl_name,
            verify_ssl=True,
            ca_cert=ssl_name,
        )

        # Create ACS using "Custom" option with content type of "Yum"
        # and using NO authentication
        session.acs.create_new_acs(
            custom_type=True,
            content_type='yum',
            name='customYumNoneAuth',
            description='customYumNoneAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            subpaths=['test/'],
            none_auth=True,
        )

        # Create ACS using "Custom" option with content type of "File"
        # and using NO authentication
        session.acs.create_new_acs(
            custom_type=True,
            content_type='file',
            name='customFileNoneAuth',
            description='customFileNoneAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            subpaths=['test/'],
            none_auth=True,
        )

        # Create ACS using "RHUI" option
        # and using content credentials authentication
        session.acs.create_new_acs(
            rhui_type=True,
            name='rhuiYumContentAuth',
            description='rhuiYumContentAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com/pulp/content',
            subpaths=['test/', 'test2/'],
            content_credentials_auth=True,
            ssl_client_cert=ssl_name,
            ssl_client_key=ssl_name,
            verify_ssl=True,
            ca_cert=ssl_name,
        )

        # Create ACS using "RHUI" option
        # and using NO authentication
        session.acs.create_new_acs(
            rhui_type=True,
            name='rhuiYumNoneAuth',
            description='rhuiYumNoneAuthDesc',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com/pulp/content',
            subpaths=['test/', 'test2/'],
            none_auth=True,
            verify_ssl=True,
            ca_cert=ssl_name,
        )

        # Create ACS on which deletion is going to be tested
        session.acs.create_new_acs(
            rhui_type=True,
            name='testAcsToBeDeleted',
            description='testAcsToBeDeleted',
            capsules_to_add=target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com/pulp/content',
            subpaths=['test/', 'test2/'],
            none_auth=True,
            verify_ssl=True,
            ca_cert=ssl_name,
        )

        # Delete ACS and check if trying to read it afterwards fails
        session.acs.delete_acs(acs_name='testAcsToBeDeleted')
        with pytest.raises(ValueError):
            session.acs.get_row_drawer_content(acs_name='testAcsToBeDeleted')

        # Refresh ACS and check that last refresh time is updated
        session.acs.refresh_acs(acs_name='simpleFile')
        simple_file_refreshed = session.acs.get_row_drawer_content(acs_name='simpleFile')
        assert (
            simple_file_refreshed['details']['last_refresh'] == 'less than a minute ago'
            or '1 minute ago'
        )

        # Rename and change description of ACS and then check that it was changed
        simple_file_renamed = session.acs.edit_acs_details(
            acs_name_to_edit='simpleFile',
            new_acs_name='simpleFileRenamed',
            new_description='simpleFileRenamedDesc',
        )
        simple_file_renamed = session.acs.get_row_drawer_content(acs_name='simpleFileRenamed')
        assert (
            simple_file_renamed['details']['details_stack_content']['name'] == 'simpleFileRenamed'
        )
        assert (
            simple_file_renamed['details']['details_stack_content']['description']
            == 'simpleFileRenamedDesc'
        )

        # Edit ACS capsules
        custom_file_edited_capsules = session.acs.edit_capsules(
            acs_name_to_edit='customFileContentAuth', remove_all=True, use_http_proxies=False
        )
        custom_file_edited_capsules = session.acs.get_row_drawer_content(
            acs_name='customFileContentAuth'
        )
        assert (
            custom_file_edited_capsules['capsules']['capsules_stack_content']['capsules_list'] == []
        )
        assert (
            custom_file_edited_capsules['capsules']['capsules_stack_content']['use_http_proxies']
            == 'false'
        )

        # Edit ACS urls and subpaths
        custom_yum_edited_url = session.acs.edit_url_subpaths(
            acs_name_to_edit='customYumNoneAuth',
            new_url='https://testNEW.com',
            new_subpaths=['test/', 'testNEW/'],
        )
        custom_yum_edited_url = session.acs.get_row_drawer_content(acs_name='customYumNoneAuth')
        assert (
            custom_yum_edited_url['url_and_subpaths']['url_and_subpaths_stack_content']['url']
            == 'https://testNEW.com'
        )
        assert (
            custom_yum_edited_url['url_and_subpaths']['url_and_subpaths_stack_content']['subpaths']
            == 'test/,testNEW/'
        )

        # Edit ACS credentials
        custom_file_edited_credentials = session.acs.edit_credentials(
            acs_name_to_edit='customFileManualAuth',
            verify_ssl=False,
            manual_auth=True,
            username='changedUserName',
        )
        custom_file_edited_credentials = session.acs.get_row_drawer_content(
            acs_name='customFileManualAuth'
        )
        assert (
            custom_file_edited_credentials['credentials']['credentials_stack_content']['verify_ssl']
            == 'false'
        )
        assert (
            custom_file_edited_credentials['credentials']['credentials_stack_content']['username']
            == 'changedUserName'
        )

        # Edit ACS products
        simple_yum_edited_products = session.acs.edit_products(
            acs_name_to_edit='simpleYum',
            remove_all=True,
        )
        simple_yum_edited_products = session.acs.get_row_drawer_content(acs_name='simpleYum')
        assert (
            simple_yum_edited_products['products']['products_stack_content']['products_list'] == []
        )
