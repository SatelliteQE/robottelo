import pytest
import requests
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import FOREMAN_TEMPLATE_ROOT_DIR


@pytest.fixture()
def create_import_export_local_dir(target_sat):
    """Creates a local directory inside root_dir on satellite from where the templates will
        be imported from or exported to.

    Also copies example template to that directory for test operations

    Finally, Removes a local directory after test is completed as a teardown part.
    """
    dir_name = gen_string('alpha')
    root_dir = FOREMAN_TEMPLATE_ROOT_DIR
    dir_path = f'{root_dir}/{dir_name}'
    # Creating the directory and set the write context
    target_sat.execute(
        f'mkdir -p {dir_path} && '
        f'chown foreman -R {root_dir} && '
        f'restorecon -R -v {root_dir} && '
        f'chcon -t httpd_sys_rw_content_t {dir_path} -R'
    )
    # Copying the file to new directory to be modified by tests
    target_sat.execute(f'cp example_template.erb {dir_path}')
    yield dir_name, dir_path
    target_sat.execute(f'rm -rf {dir_path}')


@pytest.fixture(scope='session')
def git_port(session_target_sat):
    """Allow port for git service"""
    session_target_sat.execute(f'semanage port -a -t http_port_t -p tcp {settings.git.http_port}')
    session_target_sat.execute(f'semanage port -a -t ssh_port_t -p tcp {settings.git.ssh_port}')


@pytest.fixture(scope='session')
def git_pub_key(session_target_sat, git_port):
    """Copy ssh public key to git service"""
    git = settings.git
    key_path = '/usr/share/foreman/.ssh'
    session_target_sat.execute(
        f'sudo -u foreman ssh-keygen -q -t rsa -f {key_path}/id_rsa -N "" <<<y'
    )
    key = session_target_sat.execute(f'cat {key_path}/id_rsa.pub').stdout.strip()
    title = gen_string('alpha')
    auth = (git.username, git.password)
    url = f'http://{git.hostname}:{git.http_port}'
    res = requests.post(
        f'{url}/api/v1/user/keys',
        auth=auth,
        json={'key': key, 'title': title},
    )
    res.raise_for_status()
    id = res.json()['id']
    # add ssh key to known host
    session_target_sat.execute(
        f'ssh-keyscan -t rsa -p {git.ssh_port} {git.hostname} > {key_path}/known_hosts'
    )
    yield
    res = requests.delete(
        f'{url}/api/v1/user/keys/{id}',
        auth=auth,
    )
    res.raise_for_status()


@pytest.fixture(scope='function')
def git_repository(git_port, git_pub_key, request):
    """Creates a new repository on git provider for exporting templates.

    Finally, deletes repository from git provider after tests are completed as a teardown part.
    """
    auth = (settings.git.username, settings.git.password)
    url = f'http://{settings.git.hostname}:{settings.git.http_port}'
    name = gen_string('alpha')
    res = requests.post(
        f'{url}/api/v1/user/repos',
        auth=auth,
        json={'name': name, 'auto_init': request.param, 'default_branch': 'master'},
    )
    res.raise_for_status()
    yield {'name': name, 'init': request.param}
    res = requests.delete(f'{url}/api/v1/repos/{settings.git.username}/{name}', auth=auth)
    res.raise_for_status()


@pytest.fixture()
def git_branch(git_repository):
    """Creates a new branch in the git repository for exporting templates.

    Finally, removes branch from the git repository after test is completed as a teardown part.
    """
    if git_repository['init']:
        auth = (settings.git.username, settings.git.password)
        path = f'/api/v1/repos/{settings.git.username}/{git_repository["name"]}/branches'
        url = f'http://{settings.git.hostname}:{settings.git.http_port}{path}'
        new_branch = gen_string('alpha')
        res = requests.post(
            url, auth=auth, json={'new_branch_name': new_branch, 'old_branch_name': 'master'}
        )
        res.raise_for_status()
        yield new_branch
        res = requests.delete(f'{url}/{new_branch}', auth=auth)
        res.raise_for_status()
    else:
        yield 'master'
