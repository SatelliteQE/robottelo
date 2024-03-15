"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseComponent: Puppet

:CaseImportance: Medium

:Team: Rocket

"""
import pytest

from robottelo.config import settings
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def module_puppet(session_puppet_enabled_sat, module_puppet_org, module_puppet_loc):
    puppet_class = 'cli_test_classparameters'
    env_name = session_puppet_enabled_sat.create_custom_environment(repo=puppet_class)
    session_puppet_enabled_sat.cli.Environment.update(
        {
            'name': env_name,
            'organization-ids': module_puppet_org.id,
            'location-ids': module_puppet_loc.id,
        }
    )
    puppet_class = session_puppet_enabled_sat.cli.Puppet.info(
        {'name': puppet_class, 'puppet-environment': env_name}
    )
    env = (
        session_puppet_enabled_sat.api.Environment()
        .search(query={'search': f'name="{env_name}"'})[0]
        .read()
    )
    yield {'env': env, 'class': puppet_class}
    session_puppet_enabled_sat.delete_puppet_class(puppet_class['name'])
    session_puppet_enabled_sat.destroy_custom_environment(env_name)


@pytest.fixture(scope='module')
def module_sc_params(session_puppet_enabled_sat, module_puppet):
    sc_params_list = session_puppet_enabled_sat.cli.SmartClassParameter.list(
        {
            'puppet-environment': module_puppet['env'].name,
            'search': f'puppetclass="{module_puppet["class"]["name"]}"',
        }
    )
    sc_params_ids_list = [sc_param['id'] for sc_param in sc_params_list]
    return {'list': sc_params_list, 'ids': sc_params_ids_list}


@pytest.mark.tier1
@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.skipif(
    not settings.robottelo.REPOS_HOSTING_URL, reason="repos_hosting_url is not defined"
)
class TestSmartClassParameters:
    """Implements Smart Class Parameter tests in CLI"""

    @pytest.mark.e2e
    def test_positive_list(
        self,
        request,
        session_puppet_enabled_sat,
        module_puppet_org,
        module_puppet_loc,
        module_puppet,
        module_sc_params,
    ):
        """List all the parameters included in specific elements.

        :id: 9fcfbe32-d388-435d-a629-6969a50a4243

        :expectedresults: Parameters listed for specific Environment
            (by name and id), Host (name, id), Hostgroup (name, id),
            and puppetclass (name)
        """
        host = session_puppet_enabled_sat.api.Host(
            organization=module_puppet_org.id,
            location=module_puppet_loc.id,
            environment=module_puppet['env'].name,
        ).create()
        request.addfinalizer(host.delete)
        host.add_puppetclass(data={'puppetclass_id': module_puppet['class']['id']})
        hostgroup = session_puppet_enabled_sat.cli_factory.hostgroup(
            {
                'puppet-environment-id': module_puppet['env'].id,
                'puppet-class-ids': module_puppet['class']['id'],
            }
        )

        list_queries = [
            {'puppet-environment': module_puppet['env'].name},
            {'puppet-environment-id': module_puppet['env'].id},
            {'host': host.name},
            {'host-id': host.id},
            {'hostgroup': hostgroup["name"]},
            {'hostgroup-id': hostgroup["id"]},
            {'puppet-class': module_puppet['class']['name']},
        ]

        # override an example parameter
        sc_param_id = module_sc_params['ids'].pop()
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {'id': sc_param_id, 'override': 1}
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['override'] is True

        # check listing parameters for selected queries
        for query in list_queries:
            sc_params = session_puppet_enabled_sat.cli.SmartClassParameter.list(query)
            assert len(sc_params) > 0, f"Failed to list parameters for query: {query}"
            assert sc_param_id in [scp['id'] for scp in sc_params]
            # Check that only unique results are returned
            assert len(sc_params) == len(
                {scp['id'] for scp in sc_params}
            ), f'Not only unique results returned for query: {query}'

    def test_positive_list_with_non_admin_user(self, session_puppet_enabled_sat, module_puppet):
        """List all the parameters for specific puppet class by id.

        :id: 00fbf150-34fb-45d0-80e9-d5798d24a24f

        :expectedresults: Parameters listed for specific Puppet class.

        :BZ: 1391556
        """
        password = gen_string('alpha')
        required_user_permissions = {
            'ForemanPuppet::Puppetclass': {'permissions': ['view_puppetclasses']},
            'ForemanPuppet::PuppetclassLookupKey': {
                'permissions': [
                    'view_external_parameters',
                    'create_external_parameters',
                    'edit_external_parameters',
                    'destroy_external_parameters',
                ]
            },
        }
        user = session_puppet_enabled_sat.cli_factory.user({'admin': '0', 'password': password})
        role = session_puppet_enabled_sat.cli_factory.make_role()
        session_puppet_enabled_sat.cli_factory.add_role_permissions(
            role['id'], required_user_permissions
        )

        # Add the created and initiated role with permissions to user
        session_puppet_enabled_sat.cli.User.add_role({'id': user['id'], 'role-id': role['id']})
        sc_params = session_puppet_enabled_sat.cli.SmartClassParameter.with_user(
            user['login'], password
        ).list({'puppet-class-id': module_puppet['class']['id']})
        assert len(sc_params) > 0
        # Check that only unique results are returned
        assert len(sc_params) == len({scp['id'] for scp in sc_params})

    @pytest.mark.e2e
    def test_positive_override(self, session_puppet_enabled_sat, module_puppet, module_sc_params):
        """Override the Default Parameter value.

        :id: 25e34bac-084c-4b68-a082-822633e19f7e

        :steps:

            1.  Override the parameter.
            2.  Set the new valid Default Value.
            3.  Set puppet default value to 'Use Puppet Default'.
            4.  Submit the changes.

        :expectedresults: Parameter Value overridden with new value.

        :BZ: 1830834

        :customerscenario: true
        """
        sc_param_id = module_sc_params['ids'].pop()
        value = gen_string('alpha')
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {'default-value': value, 'omit': 1, 'id': sc_param_id, 'override': 1}
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['default-value'] == value
        assert sc_param['omit'] is True

    def test_negative_override(self, session_puppet_enabled_sat, module_sc_params):
        """Override the Default Parameter value - override Unchecked.

        :id: eb24c44d-0e34-40a3-aa3e-05a3cd4ed1ea

        :steps:
            1.  Don't override the parameter.
            2.  Set the new valid Default Value.
            3.  Attempt to submit the changes.

        :expectedresults: Not overridden parameter value cannot be updated.

        :BZ: 1830834

        :customerscenario: true
        """
        sc_param_id = module_sc_params['ids'].pop()
        with pytest.raises(CLIReturnCodeError):
            session_puppet_enabled_sat.cli.SmartClassParameter.update(
                {'default-value': gen_string('alpha'), 'id': sc_param_id}
            )

    def test_negative_validate_default_value_with_list(
        self, session_puppet_enabled_sat, module_puppet, module_sc_params
    ):
        """Error raised for default value not in list.

        :id: cdcafbea-612e-4b60-90de-fa0c76442bbe

        :steps:

            1.  Override the parameter.
            2.  Provide default value that doesn't matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for default value not in list.

        :customerscenario: true
        """
        value = gen_string('alphanumeric')
        sc_param_id = module_sc_params['ids'].pop()
        with pytest.raises(CLIReturnCodeError):
            session_puppet_enabled_sat.cli.SmartClassParameter.update(
                {
                    'id': sc_param_id,
                    'default-value': value,
                    'override': 1,
                    'validator-type': 'list',
                    'validator-rule': '5, test',
                }
            )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['default-value'] != value

    @pytest.mark.e2e
    def test_positive_validate_default_value_with_list(
        self, session_puppet_enabled_sat, module_puppet, module_sc_params
    ):
        """Error not raised for default value in list and required

        :id: b03708e8-e597-40fb-bb24-a1ac87475846

        :steps:

            1.  Override the parameter.
            2.  Provide default value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value in list.

        :customerscenario: true

        :BZ: 1830834
        """
        sc_param_id = module_sc_params['ids'].pop()
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {
                'id': sc_param_id,
                'default-value': 'test',
                'override': 1,
                'validator-type': 'list',
                'validator-rule': '5, test',
                'required': 1,
            }
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['default-value'] == 'test'
        assert sc_param['validator']['type'] == 'list'
        assert sc_param['validator']['rule'] == '5, test'

    def test_negative_validate_matcher_non_existing_attribute(
        self, session_puppet_enabled_sat, module_sc_params
    ):
        """Error while creating matcher for Non Existing Attribute.

        :id: 5223e582-81b4-442d-b4ba-b16ede460ef6

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with non existing attribute in org.
            3.  Attempt to submit the change.

        :expectedresults: Error raised for non existing attribute.
        """
        sc_param_id = module_sc_params['ids'].pop()
        with pytest.raises(CLIReturnCodeError):
            session_puppet_enabled_sat.cli.SmartClassParameter.add_matcher(
                {
                    'smart-class-parameter-id': sc_param_id,
                    'match': 'hostgroup=nonexistingHG',
                    'value': gen_string('alpha'),
                }
            )

    @pytest.mark.e2e
    def test_positive_create_and_remove_matcher(
        self, session_puppet_enabled_sat, module_puppet, module_sc_params
    ):
        """Create and remove matcher for attribute in parameter.

        :id: 37fe299b-1e81-4faf-b1c3-2edfc3d53dc1

        :steps:
            1.  Override the parameter.
            2.  Set some default Value.
            3.  Create a matcher with all valid values.
            4.  Create matcher with valid attribute type, name and puppet
                default value.
            5.  Submit the change.
            6.  Remove the matcher created in step 1

        :expectedresults: The matcher has been created successfully.
        """
        sc_param_id = module_sc_params['ids'].pop()
        value = gen_string('alpha')
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {'id': sc_param_id, 'override': 1, 'override-value-order': 'is_virtual'}
        )
        session_puppet_enabled_sat.cli.SmartClassParameter.add_matcher(
            {'smart-class-parameter-id': sc_param_id, 'match': 'is_virtual=true', 'value': value}
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['override-values']['values']['1']['match'] == 'is_virtual=true'
        assert sc_param['override-values']['values']['1']['value'] == value

        session_puppet_enabled_sat.cli.SmartClassParameter.remove_matcher(
            {
                'smart-class-parameter-id': sc_param_id,
                'id': sc_param['override-values']['values']['1']['id'],
            }
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert len(sc_param['override-values']['values']) == 0

    @pytest.mark.e2e
    def test_positive_create_matcher_puppet_default_value(
        self, session_puppet_enabled_sat, module_puppet, module_sc_params
    ):
        """Create matcher for attribute in parameter, where Value is puppet default value

        :id: c08fcf25-e5c7-411e-beed-3741a24496fd

        :steps:
            1.  Override the parameter.
            2.  Set some default Value.
            3.  Create matcher with valid attribute type, name and puppet
                default value.
            4.  Submit the change.

        :expectedresults: The matcher has been created successfully.
        """
        sc_param_id = module_sc_params['ids'].pop()
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {'id': sc_param_id, 'override': 1, 'default-value': gen_string('alpha')}
        )
        session_puppet_enabled_sat.cli.SmartClassParameter.add_matcher(
            {'smart-class-parameter-id': sc_param_id, 'match': 'domain=test.com', 'omit': 1}
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['override-values']['values']['1']['match'] == 'domain=test.com'

    @pytest.mark.e2e
    def test_positive_test_hidden_parameter_value(
        self, session_puppet_enabled_sat, module_puppet, module_sc_params
    ):
        """Unhide the default value of parameter.

        :id: 3daf662f-a0dd-469c-8088-262bfaa5246a

        :steps:
            1. Set the override flag for the parameter.
            2. Set some valid default value.
            3. Set 'Hidden Value' to true and submit.
            4. After hiding, set the 'Hidden Value' to false.
            5. Update the hidden value to empty value
            6. Unhide the variable

        :expectedresults:
            1. The 'hidden value' is corrctly created
            2. It is successfull updated
            3. It remains hidden when empty
            4. It is successfully unhidden

        :CaseImportance: Low
        """
        # Create with hidden value
        sc_param_id = module_sc_params['ids'].pop()
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {
                'id': sc_param_id,
                'override': 1,
                'default-value': gen_string('alpha'),
                'hidden-value': 1,
            }
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['hidden-value?'] is True

        # Update to empty value
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {'id': sc_param_id, 'override': 1, 'hidden-value': 1, 'default-value': ''}
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id, 'show-hidden': 1}
        )
        assert sc_param['default-value'] == ''
        assert sc_param['hidden-value?'] is True

        # Unhide
        session_puppet_enabled_sat.cli.SmartClassParameter.update(
            {'id': sc_param_id, 'hidden-value': 0}
        )
        sc_param = session_puppet_enabled_sat.cli.SmartClassParameter.info(
            {'puppet-class': module_puppet['class']['name'], 'id': sc_param_id}
        )
        assert sc_param['default-value'] == ''
        assert sc_param['hidden-value?'] is False
