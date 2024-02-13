# Alternate Content Sources fixtures
import pytest

from robottelo.config import settings


@pytest.fixture(scope='module')
def module_yum_repo(module_target_sat, module_org):
    product = module_target_sat.api.Product(organization=module_org).create()
    repo = module_target_sat.api.Repository(
        product=product,
        content_type='yum',
        url=settings.repos.yum_0.url,
    ).create()
    repo.sync()
    return repo


@pytest.fixture(scope='module')
def module_file_repo(module_target_sat, module_org):
    product = module_target_sat.api.Product(organization=module_org).create()
    repo = module_target_sat.api.Repository(
        product=product,
        content_type='file',
        url=settings.repos.file_type_repo.url,
    ).create()
    repo.sync()
    return repo
