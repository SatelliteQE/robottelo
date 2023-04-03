# Alternate Content Sources fixtures
import pytest

from robottelo.constants.repos import CUSTOM_FILE_REPO
from robottelo.constants.repos import CUSTOM_RPM_REPO


@pytest.fixture(scope='module')
def module_yum_repo(module_target_sat, module_org):
    product = module_target_sat.api.Product(organization=module_org).create()
    repo = module_target_sat.api.Repository(
        product=product, content_type='yum', url=CUSTOM_RPM_REPO
    ).create()
    repo.sync()
    return repo


@pytest.fixture(scope='module')
def module_file_repo(module_target_sat, module_org):
    product = module_target_sat.api.Product(organization=module_org).create()
    repo = module_target_sat.api.Repository(
        product=product, content_type='file', url=CUSTOM_FILE_REPO
    ).create()
    repo.sync()
    return repo
