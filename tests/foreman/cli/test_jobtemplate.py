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


@pytest.mark.tier1
def test_positive_create_job_template(module_org, module_target_sat):
    """Create a simple Job Template

    :id: a5a67b10-61b0-4362-b671-9d9f095c452c

    :expectedresults: The job template was successfully created

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
    assert module_target_sat.cli.JobTemplate.info({'name': template_name}) is not None


@pytest.mark.tier1
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


@pytest.mark.tier1
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


@pytest.mark.tier1
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


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_job_template(module_org, module_target_sat):
    """Delete a job template

    :id: 33104c04-20e9-47aa-99da-4bf3414ea31a

    :expectedresults: The Job Template has been deleted

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
    module_target_sat.cli.JobTemplate.delete({'name': template_name})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.JobTemplate.info({'name': template_name})


@pytest.mark.tier2
def test_positive_view_dump(module_org, module_target_sat):
    """Export contents of a job template

    :id: 25fcfcaa-fc4c-425e-919e-330e36195c4a

    :expectedresults: Verify no errors are thrown
    """
    template_name = gen_string('alpha', 7)
    module_target_sat.cli_factory.job_template(
        {
            'organizations': module_org.name,
            'name': template_name,
            'file': TEMPLATE_FILE,
        }
    )
    dumped_content = module_target_sat.cli.JobTemplate.dump({'name': template_name})
    assert len(dumped_content) > 0
