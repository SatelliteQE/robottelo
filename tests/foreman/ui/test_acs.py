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
from robottelo.constants import REPO_TYPE
from robottelo.constants.repos import CUSTOM_FILE_REPO
from robottelo.utils.datafactory import gen_string

ssl_name, product_name, product_label, product_description, repository_name = (
    gen_string('alpha') for _ in range(5)
)
repos_to_enable = ['rhae2.9_el8']


@pytest.fixture(scope='class')
def acs_setup(class_target_sat, module_sca_manifest_org):
    """
    This fixture creates all the necessary data for the test to run.
    It creates an organization, content credentials, product and repositories.
    """
    class_target_sat.api.ContentCredential(
        name=ssl_name,
        content=gen_string('alpha'),
        organization=module_sca_manifest_org.id,
        content_type="cert",
    ).create()

    product = class_target_sat.api.Product(
        name=product_name, organization=module_sca_manifest_org.id
    ).create()

    class_target_sat.api.Repository(
        product=product, content_type=REPO_TYPE['file'], url=CUSTOM_FILE_REPO
    ).create()

    for repo in repos_to_enable:
        class_target_sat.cli.RepositorySet.enable(
            {
                'organization-id': module_sca_manifest_org.id,
                'name': constants.REPOS[repo]['reposet'],
                'product': constants.REPOS[repo]['product'],
                'releasever': constants.REPOS[repo]['version'],
                'basearch': constants.DEFAULT_ARCHITECTURE,
            }
        )

    return class_target_sat, module_sca_manifest_org


class TestAllAcsTypes:
    """
    Test class insuring fixture is ran once before
    test_check_all_acs_types_can_be_created
    """

    pytestmark = pytest.mark.usefixtures('acs_setup')

    @pytest.mark.parametrize('cnt_type', ['yum', 'file'])
    @pytest.mark.parametrize('acs_type', ['custom', 'simplified', 'rhui'])
    def test_check_all_acs_types_can_be_created(self, session, cnt_type, acs_type, acs_setup):
        """
        This test creates all possible ACS types.

        :id cbd0f4e6-2151-446a-90d3-69c6935a0c91

        :parametrized: yes

        :steps:
            1. Select an organization
            2. Create ACSes (randomly selected ones)
            3. Test refresh
            4. Test renaming and changing description
            5. Test editing capsules
            6. Test editing urls and subpaths
            7. Test editing credentials
            8. Test editing products
            9. Create ACS on which deletion is going to be tested
            10. Test deletion
        :expectedresults:
            This test should create some
            Aleternate Content Sources and asserts that actions
            were made correctly on them.

        """

        if acs_type == 'rhui' and cnt_type == 'file':
            pytest.skip('Unsupported parameter combination.')

        class_target_sat, module_sca_manifest_org = acs_setup
        with class_target_sat.ui_session() as session:
            session.organization.select(org_name=module_sca_manifest_org.name)

            match acs_type:
                case 'simplified':

                    if cnt_type == 'yum':
                        # Create ACS using "Simplified" option with content type of "Yum"
                        session.acs.create_new_acs(
                            simplified_type=True,
                            content_type='yum',
                            name='simpleYum',
                            description='simpleYumDesc',
                            capsules_to_add=class_target_sat.hostname,
                            use_http_proxies=True,
                            products_to_add=[
                                constants.REPOS[repo]['product'] for repo in repos_to_enable
                            ],
                        )

                    if cnt_type == 'file':
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

                case 'custom':

                    if cnt_type == 'yum':
                        # Create ACS using "Custom" option with content type of "Yum"
                        # and using manual authentication
                        session.acs.create_new_acs(
                            custom_type=True,
                            content_type='yum',
                            name='customYumManualAuth',
                            description='customYumManualAuthDesc',
                            capsules_to_add=class_target_sat.hostname,
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
                            capsules_to_add=class_target_sat.hostname,
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
                            capsules_to_add=class_target_sat.hostname,
                            use_http_proxies=True,
                            base_url='https://test.com',
                            subpaths=['test/'],
                            none_auth=True,
                        )

                    if cnt_type == 'file':
                        # Create ACS using "Custom" option with content type of "File"
                        # and using content credentials authentication
                        session.acs.create_new_acs(
                            custom_type=True,
                            content_type='file',
                            name='customFileContentAuth',
                            description='customFileContentAuthDesc',
                            capsules_to_add=class_target_sat.hostname,
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
                        # and using NO authentication
                        session.acs.create_new_acs(
                            custom_type=True,
                            content_type='file',
                            name='customFileNoneAuth',
                            description='customFileNoneAuthDesc',
                            capsules_to_add=class_target_sat.hostname,
                            use_http_proxies=True,
                            base_url='https://test.com',
                            subpaths=['test/'],
                            none_auth=True,
                        )

                        # Create ACS using "Custom" option with content type of "File"
                        # and using manual authentication
                        session.acs.create_new_acs(
                            custom_type=True,
                            content_type='file',
                            name='customFileManualAuth',
                            description='customFileManualAuthDesc',
                            capsules_to_add=class_target_sat.hostname,
                            use_http_proxies=True,
                            base_url='https://test.com',
                            subpaths=['test/'],
                            manual_auth=True,
                            username='test',
                            password='test',
                            verify_ssl=True,
                            ca_cert=ssl_name,
                        )

                case 'rhui':
                    # Create ACS using "RHUI" option
                    # and using content credentials authentication
                    session.acs.create_new_acs(
                        rhui_type=True,
                        name='rhuiYumContentAuth',
                        description='rhuiYumContentAuthDesc',
                        capsules_to_add=class_target_sat.hostname,
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
                        capsules_to_add=class_target_sat.hostname,
                        use_http_proxies=True,
                        base_url='https://test.com/pulp/content',
                        subpaths=['test/', 'test2/'],
                        none_auth=True,
                        verify_ssl=True,
                        ca_cert=ssl_name,
                    )


class TestAcsE2e:
    """
    Test class insuring fixture is ran once before
    test_acs_positive_end_to_end
    """

    pytestmark = pytest.mark.usefixtures('acs_setup')

    @pytest.mark.e2e
    def test_acs_positive_end_to_end(self, session, acs_setup):
        """
        Create, update, delete and refresh ACSes.

        :id: 047452cc-5a9f-4473-96b1-d5b6830b7d6b

        :steps:
            1. Select an organization
            2. Create ACSes (randomly selected ones)
            3. Test refresh
            4. Test renaming and changing description
            5. Test editing capsules
            6. Test editing urls and subpaths
            7. Test editing credentials
            8. Test editing products
            9. Create ACS on which deletion is going to be tested
            10. Test deletion
        :expectedresults:
            This test should create some
            Aleternate Content Sources and asserts that actions
            were made correctly on them.
        """

        class_target_sat, module_sca_manifest_org = acs_setup

        with class_target_sat.ui_session() as session:
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
                capsules_to_add=class_target_sat.hostname,
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
                capsules_to_add=class_target_sat.hostname,
                use_http_proxies=True,
                base_url='https://test.com',
                subpaths=['test/'],
                manual_auth=True,
                username='test',
                password='test',
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
                capsules_to_add=class_target_sat.hostname,
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
                capsules_to_add=class_target_sat.hostname,
                use_http_proxies=True,
                base_url='https://test.com',
                subpaths=['test/'],
                none_auth=True,
            )

            # Refresh ACS and check that last refresh time is updated
            session.acs.refresh_acs(acs_name='simpleFile')
            simple_file_refreshed = session.acs.get_row_drawer_content(acs_name='simpleFile')
            assert simple_file_refreshed['details']['last_refresh'] in [
                'less than a minute ago',
                '1 minute ago',
            ]

            # Rename and change description of ACS and then check that it was changed
            simple_file_renamed = session.acs.edit_acs_details(
                acs_name_to_edit='simpleFile',
                new_acs_name='simpleFileRenamed',
                new_description='simpleFileRenamedDesc',
            )
            simple_file_renamed = session.acs.get_row_drawer_content(acs_name='simpleFileRenamed')
            assert (
                simple_file_renamed['details']['details_stack_content']['name']
                == 'simpleFileRenamed'
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
                custom_file_edited_capsules['capsules']['capsules_stack_content']['capsules_list']
                == []
            )
            assert (
                custom_file_edited_capsules['capsules']['capsules_stack_content'][
                    'use_http_proxies'
                ]
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
                custom_yum_edited_url['url_and_subpaths']['url_and_subpaths_stack_content'][
                    'subpaths'
                ]
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
                custom_file_edited_credentials['credentials']['credentials_stack_content'][
                    'verify_ssl'
                ]
                == 'false'
            )
            assert (
                custom_file_edited_credentials['credentials']['credentials_stack_content'][
                    'username'
                ]
                == 'changedUserName'
            )

            # Edit ACS products
            simple_yum_edited_products = session.acs.edit_products(
                acs_name_to_edit='simpleYum',
                remove_all=True,
            )
            simple_yum_edited_products = session.acs.get_row_drawer_content(acs_name='simpleYum')
            assert (
                simple_yum_edited_products['products']['products_stack_content']['products_list']
                == []
            )

            # Create ACS on which deletion is going to be tested
            session.acs.create_new_acs(
                rhui_type=True,
                name='testAcsToBeDeleted',
                description='testAcsToBeDeleted',
                capsules_to_add=class_target_sat.hostname,
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
