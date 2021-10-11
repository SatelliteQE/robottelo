import pytest
import requests
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import FOREMAN_TEMPLATE_ROOT_DIR


@pytest.fixture()
def create_import_export_local_dir(default_sat):
    """Creates a local directory inside root_dir on satellite from where the templates will
        be imported from or exported to.

    Also copies example template to that directory for test operations

    Finally, Removes a local directory after test is completed as a teardown part.
    """
    dir_name = gen_string('alpha')
    root_dir = FOREMAN_TEMPLATE_ROOT_DIR
    dir_path = f'{root_dir}/{dir_name}'
    # Creating the directory and set the write context
    default_sat.execute(
        f'mkdir -p {dir_path} && '
        f'chown foreman -R {root_dir} && '
        f'restorecon -R -v {root_dir} && '
        f'chcon -t httpd_sys_rw_content_t {dir_path} -R'
    )
    # Copying the file to new directory to be modified by tests
    default_sat.execute(f'cp example_template.erb {dir_path}')
    yield dir_name, dir_path
    default_sat.execute(f'rm -rf {dir_path}')


@pytest.fixture(scope='session')
def git_repository():
    """Creates a new repository on git provider for exporting templates.

    Finally, deletes repository from git provider after tests are completed as a teardown part.
    """
    auth = (settings.git.username, settings.git.password)
    name = gen_string('alpha')
    res = requests.post(
        f"{settings.git.url}/api/v1/user/repos",
        auth=auth,
        json={"name": name, "auto_init": True, "default_branch": "master"},
    )
    assert res.status_code == 201
    yield name
    res = requests.delete(
        f"{settings.git.url}/api/v1/repos/{settings.git.username}/{name}", auth=auth
    )
    assert res.status_code == 204


@pytest.fixture()
def git_branch(git_repository):
    """Creates a new branch in the git repository for exporting templates.

    Finally, removes branch from the git repository after test is completed as a teardown part.
    """
    auth = (settings.git.username, settings.git.password)
    url = f"{settings.git.url}/api/v1/repos/{settings.git.username}/{git_repository}/branches"
    new_branch = gen_string('alpha')
    res = requests.post(
        url, auth=auth, json={"new_branch_name": new_branch, "old_branch_name": "master"}
    )
    assert res.status_code == 201
    yield new_branch
    res = requests.delete(f'{url}/{new_branch}', auth=auth)
    assert res.status_code == 204
