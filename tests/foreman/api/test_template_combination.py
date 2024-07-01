"""Tests for template combination

:Requirement: TemplateCombination

:CaseAutomation: Automated

:CaseComponent: ProvisioningTemplates

:Team: Rocket

"""

import pytest
from requests.exceptions import HTTPError


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_end_to_end_template_combination(request, module_target_sat, module_hostgroup):
    """Assert API template combination get/delete method works.

    :id: 3a5cb370-c5f6-11e6-bb2f-68f72889dc7g

    :Setup: save a template combination

    :expectedresults: TemplateCombination can be created, retrieved and deleted through API

    :CaseImportance: Critical

    :BZ: 1369737
    """
    template = module_target_sat.api.ProvisioningTemplate(
        snippet=False,
        template_combinations=[
            {
                'hostgroup_id': module_hostgroup.id,
            }
        ],
    )
    template = template.create()
    template_combination_dct = template.template_combinations[0]
    template_combination = module_target_sat.api.TemplateCombination(
        id=template_combination_dct['id'],
        provisioning_template=template,
        hostgroup=module_hostgroup,
    )
    # GET
    combination = template_combination.read()
    assert template.id == combination.provisioning_template.id
    assert module_hostgroup.id == combination.hostgroup.id

    # DELETE
    assert len(template.read().template_combinations) == 1
    combination.delete()
    with pytest.raises(HTTPError):
        combination.read()
    assert len(template.read().template_combinations) == 0
    template.delete()
    module_hostgroup.delete()
