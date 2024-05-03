"""Tests for Alternate Content Sources UI

:Requirement: AlternateContentSources

:CaseAutomation: Automated

:CaseComponent: AlternateContentSources

:Team: Phoenix-content

:CaseImportance: High

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
def acs_setup(class_target_sat, class_sca_manifest_org):
    """
    This fixture creates all the necessary data for the test to run.
    It creates an organization, content credentials, product and repositories.
    """
    class_target_sat.api.ContentCredential(
        name=ssl_name,
        content=gen_string('alpha'),
        organization=class_sca_manifest_org.id,
        content_type="cert",
    ).create()

    product = class_target_sat.api.Product(
        name=product_name, organization=class_sca_manifest_org.id
    ).create()

    class_target_sat.api.Repository(
        product=product, content_type=REPO_TYPE['file'], url=CUSTOM_FILE_REPO
    ).create()

    for repo in repos_to_enable:
        class_target_sat.cli.RepositorySet.enable(
            {
                'organization-id': class_sca_manifest_org.id,
                'name': constants.REPOS[repo]['reposet'],
                'product': constants.REPOS[repo]['product'],
                'releasever': constants.REPOS[repo]['version'],
                'basearch': constants.DEFAULT_ARCHITECTURE,
            }
        )

    return class_target_sat, class_sca_manifest_org


@pytest.mark.tier2
def test_acs_subpath_not_required(acs_setup):
    """
    This test verifies that the subpath field isn't mandatory for ACS creation.

    :id: 232d944a-a7c1-4387-ab01-7e20b2bbebfa

    :steps:
        1. Create an ACS of each type where subpath field is present in the UI

    :expectedresults:
        Subpath field isn't required in the creation of any ACS where it's present,
        so ACS should all create successfully

    :BZ: 2119112

    :customerscenario: True
    """
    class_target_sat, class_sca_manifest_org = acs_setup

    with class_target_sat.ui_session() as session:
        session.organization.select(org_name=class_sca_manifest_org.name)

        # Create an ACS of each configturation that displays the subpath field in UI
        session.acs.create_new_acs(
            custom_type=True,
            content_type='yum',
            name=gen_string('alpha'),
            capsules_to_add=class_target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            none_auth=True,
        )

        session.acs.create_new_acs(
            custom_type=True,
            content_type='file',
            name=gen_string('alpha'),
            capsules_to_add=class_target_sat.hostname,
            use_http_proxies=True,
            base_url='https://test.com',
            none_auth=True,
        )

        session.acs.create_new_acs(
            rhui_type=True,
            name=gen_string('alpha'),
            capsules_to_add=class_target_sat.hostname,
            use_http_proxies=True,
            base_url='https://rhui-server.example.com/pulp/content',
            none_auth=True,
        )


class TestAllAcsTypes:
    """
    Test class insuring fixture is ran once before
    test_check_all_acs_types_can_be_created
    """

    pytestmark = pytest.mark.usefixtures('acs_setup')

    def gen_params():
        """
        This function generates parameters that are used in test_check_all_acs_types_can_be_created.
        """

        parameters_dict = {
            '_common': {
                'use_http_proxies': True,
            },
            'custom': {
                '_common': {
                    'custom_type': True,
                    'base_url': 'https://test.com/',
                    'subpaths': ['test/'],
                    'capsules_to_add': 'class_target_sat.hostname',
                },
                'yum_manual_auth': {
                    'content_type': 'yum',
                    'name': 'customYumManualAuth',
                    'description': 'customYumManualAuthDesc',
                    'manual_auth': True,
                    'verify_ssl': True,
                    'ca_cert': ssl_name,
                    'username': 'test',
                    'password': 'test',
                },
                'yum_content_auth': {
                    'content_type': 'yum',
                    'name': 'customYumContentAuth',
                    'description': 'customYumContentAuthDesc',
                    'content_credentials_auth': True,
                    'ssl_client_cert': ssl_name,
                    'ssl_client_key': ssl_name,
                    'verify_ssl': True,
                    'ca_cert': ssl_name,
                },
                'yum_none_auth': {
                    'content_type': 'yum',
                    'name': 'customYumNoneAuth',
                    'description': 'customYumNoneAuthDesc',
                    'none_auth': True,
                },
                'file_manual_auth': {
                    'content_type': 'file',
                    'name': 'customFileManualAuth',
                    'description': 'customFileManualAuthDesc',
                    'manual_auth': True,
                    'verify_ssl': True,
                    'ca_cert': ssl_name,
                    'username': 'test',
                    'password': 'test',
                },
                'file_content_auth': {
                    'content_type': 'file',
                    'name': 'customFileContentAuth',
                    'description': 'customFileContentAuthDesc',
                    'content_credentials_auth': True,
                    'ssl_client_cert': ssl_name,
                    'ssl_client_key': ssl_name,
                    'verify_ssl': True,
                    'ca_cert': ssl_name,
                },
                'file_none_auth': {
                    'content_type': 'file',
                    'name': 'customFileNoneAuth',
                    'description': 'customFileNoneAuthDesc',
                    'none_auth': True,
                },
            },
            'simplified': {
                '_common': {'simplified_type': True},
                'yum': {
                    'content_type': 'yum',
                    'name': 'simpleYum',
                    'description': 'simpleYumDesc',
                    'capsules_to_add': 'class_target_sat.hostname',
                    'products_to_add': [
                        constants.REPOS[repo]['product'] for repo in repos_to_enable
                    ],
                },
                'file': {
                    'content_type': 'file',
                    'name': 'simpleFile',
                    'description': 'simpleFileDesc',
                    'add_all_capsules': True,
                    'products_to_add': product_name,
                },
            },
            'rhui': {
                '_common': {
                    'rhui_type': True,
                    'base_url': 'https://test.com/pulp/content',
                    'subpaths': ['test/', 'test2/'],
                    'verify_ssl': True,
                    'ca_cert': ssl_name,
                    'capsules_to_add': 'class_target_sat.hostname',
                },
                'yum_none_auth': {
                    'name': 'rhuiYumNoneAuth',
                    'description': 'rhuiYumNoneAuthDesc',
                    'none_auth': True,
                },
                'yum_content_auth': {
                    'name': 'rhuiYumContentAuth',
                    'description': 'rhuiYumContentAuthDesc',
                    'content_credentials_auth': True,
                    'ssl_client_cert': ssl_name,
                    'ssl_client_key': ssl_name,
                },
            },
        }

        ids = []
        vals = []
        # This code creates a list of scenario IDs and values for each scenario.
        # It loops through the keys in the parameters dictionary, and uses the keys to create a scenario ID
        # and then it uses the scenario ID to access the scenario values from the parameters dictionary.
        # The code then adds the scenario values to the list of scenario values.
        for acs in parameters_dict:
            if not acs.startswith('_'):
                for cnt in parameters_dict[acs]:
                    if not cnt.startswith('_'):
                        scenario = (
                            parameters_dict[acs][cnt]
                            | parameters_dict.get('_common', {})
                            | parameters_dict[acs].get('_common', {})
                        )
                        ids.append(f'{acs}_{cnt}')
                        vals.append(scenario)
        return (vals, ids)

    @pytest.mark.parametrize('scenario', gen_params()[0], ids=gen_params()[1])
    def test_check_all_acs_types_can_be_created(session, scenario, acs_setup):
        """
        This test creates all possible ACS types.

        :id: 6bfad272-3ff8-4780-b346-1229d70524b1

        :parametrized: yes

        :steps:
            1. Select an organization
            2. Create ACSes
        :expectedresults:
            This test should create all Aleternate Content Sources
        """

        class_target_sat, class_sca_manifest_org = acs_setup
        vals = scenario

        # Replace the placeholder in 'capsules_to_add' with the hostname of the Satellite under test
        for val in vals:
            if 'capsules_to_add' in val:
                vals['capsules_to_add'] = class_target_sat.hostname

        with class_target_sat.ui_session() as session:
            session.organization.select(org_name=class_sca_manifest_org.name)
            session.acs.create_new_acs(**vals)


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

        class_target_sat, class_sca_manifest_org = acs_setup

        with class_target_sat.ui_session() as session:
            session.organization.select(org_name=class_sca_manifest_org.name)

            # Create ACS using "Simplified" option with content type of "File"
            session.acs.create_new_acs(
                simplified_type=True,
                content_type='file',
                name='simpleFileTest',
                description='simpleFileTestDesc',
                add_all_capsules=True,
                use_http_proxies=True,
                products_to_add=product_name,
            )

            # Create ACS using "Simplified" option with content type of "Yum"
            session.acs.create_new_acs(
                simplified_type=True,
                content_type='yum',
                name='simpleYumTest',
                description='simpleYumTestDesc',
                capsules_to_add=class_target_sat.hostname,
                use_http_proxies=True,
                products_to_add=[constants.REPOS[repo]['product'] for repo in repos_to_enable],
            )

            # Create ACS using "Custom" option with content type of "File"
            # and using manual authentication
            session.acs.create_new_acs(
                custom_type=True,
                content_type='file',
                name='customFileManualTestAuth',
                description='customFileManualTestAuthDesc',
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
                name='customFileContentAuthTest',
                description='customFileContentAuthTestDesc',
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
                name='customYumNoneAuthTest',
                description='customYumNoneAuthTestDesc',
                capsules_to_add=class_target_sat.hostname,
                use_http_proxies=True,
                base_url='https://test.com',
                subpaths=['test/'],
                none_auth=True,
            )

            # Refresh ACS and check that last refresh time is updated
            session.acs.refresh_acs(acs_name='simpleFileTest')
            simple_file_refreshed = session.acs.get_row_drawer_content(acs_name='simpleFileTest')
            assert simple_file_refreshed['details']['last_refresh'] in [
                'less than a minute ago',
                '1 minute ago',
            ]

            # Rename and change description of ACS and then check that it was changed
            simple_file_renamed = session.acs.edit_acs_details(
                acs_name_to_edit='simpleFileTest',
                new_acs_name='simpleFileTestRenamed',
                new_description='simpleFileTestRenamedDesc',
            )
            simple_file_renamed = session.acs.get_row_drawer_content(
                acs_name='simpleFileTestRenamed'
            )
            assert (
                simple_file_renamed['details']['details_stack_content']['name']
                == 'simpleFileTestRenamed'
            )
            assert (
                simple_file_renamed['details']['details_stack_content']['description']
                == 'simpleFileTestRenamedDesc'
            )

            # Edit ACS capsules
            custom_file_edited_capsules = session.acs.edit_capsules(
                acs_name_to_edit='customFileContentAuthTest',
                remove_all=True,
                use_http_proxies=False,
            )
            custom_file_edited_capsules = session.acs.get_row_drawer_content(
                acs_name='customFileContentAuthTest'
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
                acs_name_to_edit='customYumNoneAuthTest',
                new_url='https://testNEW.com',
                new_subpaths=['test/', 'testNEW/'],
            )
            custom_yum_edited_url = session.acs.get_row_drawer_content(
                acs_name='customYumNoneAuthTest'
            )
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
                acs_name_to_edit='customFileManualTestAuth',
                verify_ssl=False,
                manual_auth=True,
                username='changedUserName',
            )
            custom_file_edited_credentials = session.acs.get_row_drawer_content(
                acs_name='customFileManualTestAuth'
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
                acs_name_to_edit='simpleYumTest',
                remove_all=True,
            )
            simple_yum_edited_products = session.acs.get_row_drawer_content(
                acs_name='simpleYumTest'
            )
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
            with pytest.raises(ValueError):  # noqa: PT011 - TODO Ladislav find better exception
                session.acs.get_row_drawer_content(acs_name='testAcsToBeDeleted')
