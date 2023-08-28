"""Plugin enables pytest to notify and update the requirements"""
import os
import re
import subprocess
from pathlib import Path
from robottelo.logging import robottelo_root_dir


def pytest_addoption(parser):
    """Options to allow user to update the requirements"""
    envpath = robottelo_root_dir.joinpath('.env')
    # check if this is being executed by a user and not automation/CI
    if (
        re.search(r'\s*#.*VAULT_SECRET_ID_FOR_DYNACONF', envpath.read_text())
        and 'VAULT_SECRET_ID_FOR_DYNACONF' not in os.environ
    ):
        vstatus = subprocess.run("make vault-status", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
        if vstatus != 0:
            print('Vault token is expired, Browser opening to logging you in ...')
            subprocess.run('make vault-login', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
