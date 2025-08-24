"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo import ssh
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.utils.datafactory import invalid_values_list, parametrized

TEMPLATE_FILE = 'template_file.txt'
TEMPLATE_FILE_EMPTY = 'template_file_empty.txt'


@pytest.fixture(scope="module", autouse=True)
def module_template():
    ssh.command(f'''echo '<%= input("command") %>' > {TEMPLATE_FILE}''')
    ssh.command(f'touch {TEMPLATE_FILE_EMPTY}')


@pytest.mark.upgrade
def test_positive_job_template_crud(module_org, module_target_sat):
    """Create and delete a simple Job Template

    :id: e765ebdf-f9fe-47af-aa32-390516e87ada

    :steps:
        1. Create a job template
        2. Update the job template
        3. Delete the job template

    :expectedresults: The job template was successfully performing CRUD operations.

    :CaseImportance: Critical
    """
    template_name = gen_string('alpha', 7)
    module_target_sat.cli_factory.job_template(
        {
            'organizations': module_org.name,
            'name': template_name,
            'file': TEMPLATE_FILE,
        }
    )
    template = module_target_sat.cli.JobTemplate.info({'name': template_name})
    assert template["name"] == template_name
    # Update job template
    new_template_name = gen_string('alpha', 7)
    module_target_sat.cli.JobTemplate.update(
        {
            'name': new_template_name,
            'id': template["id"],
            'description': gen_string('alpha'),
        }
    )
    assert module_target_sat.cli.JobTemplate.info({'name': new_template_name}) is not None
    # Delete job template
    module_target_sat.cli.JobTemplate.delete({'name': new_template_name})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.JobTemplate.info({'name': new_template_name})


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_job_template_with_invalid_name(module_org, name, module_target_sat):
    """Create Job Template with invalid name

    :id: eb51afd4-e7b3-42c3-81c3-6e18ef3d7efe

    :parametrized: yes

    :expectedresults: Job Template with invalid name cannot be created and
        error is raised

    :CaseImportance: Critical
    """
    with pytest.raises(CLIFactoryError, match='Could not create the job template:'):
        module_target_sat.cli_factory.job_template(
            {
                'organizations': module_org.name,
                'name': name,
                'file': TEMPLATE_FILE,
            }
        )


def test_negative_create_job_template_with_same_name(module_org, module_target_sat):
    """Create Job Template with duplicate name

    :id: 66100c82-97f5-4300-a0c9-8cf041f7789f

    :expectedresults: The name duplication is caught and error is raised

    :CaseImportance: Critical
    """
    template_name = gen_string('alpha', 7)
    module_target_sat.cli_factory.job_template(
        {
            'organizations': module_org.name,
            'name': template_name,
            'file': TEMPLATE_FILE,
        }
    )
    with pytest.raises(CLIFactoryError, match='Could not create the job template:'):
        module_target_sat.cli_factory.job_template(
            {
                'organizations': module_org.name,
                'name': template_name,
                'file': TEMPLATE_FILE,
            }
        )


def test_negative_create_empty_job_template(module_org, module_target_sat):
    """Create Job Template with empty template file

    :id: 749be863-94ae-4008-a242-c23f353ca404

    :expectedresults: The empty file is detected and error is raised

    :CaseImportance: Critical
    """
    template_name = gen_string('alpha', 7)
    with pytest.raises(CLIFactoryError, match='Could not create the job template:'):
        module_target_sat.cli_factory.job_template(
            {
                'organizations': module_org.name,
                'name': template_name,
                'file': TEMPLATE_FILE_EMPTY,
            }
        )


@pytest.mark.upgrade
def test_positive_clone_job_template(module_org, module_target_sat):
    """Clone a job template

    :id: 5b7c6809-9199-448c-abf2-bb160709a345

    :steps:
        1. Create a job template
        2. Clone the job template
        3. assert dump of the data of the cloned job template is working
        4. update job template to unlocked
        5. Delete the cloned job template
        6. Delete the original job template

    :expectedresults: The job template is cloned successfully

    :CaseImportance: Critical

    :verifies: SAT-34616
    """
    template_name = gen_string('alpha', 7)
    module_target_sat.cli_factory.job_template(
        {
            'organizations': module_org.name,
            'name': template_name,
            'file': TEMPLATE_FILE,
            'locked': "true",
        }
    )
    template = module_target_sat.cli.JobTemplate.info({'name': template_name})
    assert template["name"] == template_name
    # assert job is not None
    clone_name = gen_string('alpha', 7)
    module_target_sat.cli.JobTemplate.clone(
        {
            'name': clone_name,
            'id': template['id'],
        }
    )
    assert module_target_sat.cli.JobTemplate.info({'name': clone_name})['name'] == clone_name
    # assert dump of the data of the cloned job template is working
    dump = module_target_sat.cli.JobTemplate.dump({'name': clone_name})
    assert len(dump) > 0
    # update job template to unlocked
    module_target_sat.cli.JobTemplate.update(
        {
            'id': template['id'],
            'locked': "false",
        }
    )
    # Delete cloned job template
    module_target_sat.cli.JobTemplate.delete({'name': clone_name})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.JobTemplate.info({'name': clone_name})
    # Delete original job template
    module_target_sat.cli.JobTemplate.delete({'name': template_name})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.JobTemplate.info({'name': template_name})
