import pytest
from fauxfactory import gen_string

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
