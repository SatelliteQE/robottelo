"""Test class for Job Template API

:Requirement: Job Template

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest


@pytest.mark.e2e
def test_job_template_lifecycle_operations(module_org, module_target_sat):
    """Perform CRUD operations on a job template

    :id: 31d9f715-ab1d-445e-abca-defa3d10c8f7

    :steps:
        1. Create a job template with locked parameter
        2. Check if job template is created with locked parameter
        3. clone job template
        4. update job template to add description and remove lock
        5. Delete job template
        6. Check if job template is deleted
        7. Delete cloned job template
        8. Check if cloned job template is deleted

    :expectedresults: The job template is successfully created and deleted

    :CaseImportance: Critical
    """
    template_name = gen_string('alpha', 7)
    clone_name = gen_string('alpha', 7)
    clone_data = {'name': clone_name}
    description = gen_string('alpha')
    # Create job template
    job_template = module_target_sat.api.JobTemplate(
        name=template_name,
        template='<%= input("command") %>',
        organization=[module_org],
        provider_type='SSH',
        locked=True,
    ).create()
    assert job_template.name == template_name
    assert job_template.locked
    # Check if job template is created
    assert (
        module_target_sat.api.JobTemplate().search(query={'search': f'name="{template_name}"'})
        is not None
    )
    # clone job template
    clone_template = job_template.clone(data=clone_data)
    assert clone_template["name"] == clone_name
    assert clone_template["cloned_from_id"] == job_template.id
    # Update job template : description and remove lock
    job_template = module_target_sat.api.JobTemplate(
        id=job_template.id, description=description, locked=False
    ).update()
    assert job_template.description == description
    assert not job_template.locked
    # Delete job template
    module_target_sat.api.JobTemplate(id=job_template.id).delete()
    # Check if job template is deleted
    assert not module_target_sat.api.JobTemplate().search(
        query={'search': f'name="{template_name}"'}
    )
    # Delete cloned job template
    module_target_sat.api.JobTemplate(id=clone_template['id']).delete()
    # Check if cloned job template is deleted
    assert not module_target_sat.api.JobTemplate().search(query={'search': f'name="{clone_name}"'})
