#!/usr/bin/env python
# This Enables and Disables individuals OIDC token to access secrets from vault
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from robottelo.constants import Colored
from robottelo.utils import export_vault_env_vars


HELP_TEXT = (
    "Vault CLI in not installed in your system, "
    "refer link https://learn.hashicorp.com/tutorials/vault/getting-started-install to "
    "install vault CLI as per your system spec!"
)


def _vault_command(command: str):
    vcommand = subprocess.run(command, capture_output=True, shell=True)
    if vcommand.returncode != 0:
        verror = str(vcommand.stderr)
        if 'vault: command not found' in verror:
            print(f"{Colored.REDDARK}Error! {HELP_TEXT}")
            sys.exit(1)
        elif 'Error revoking token' in verror:
            print(f"{Colored.GREEN}Token is alredy revoked!")
            sys.exit(0)
        elif 'Error looking up token' in verror:
            print(f"{Colored.YELLOW}Warning! Vault not logged in, please run 'make vault-login'!")
            sys.exit(2)
        else:
            print(f"{Colored.REDDARK}Error! {verror}")
            sys.exit(1)
    return vcommand


def _vault_login(root_path, envdata):
    print(
        f"{Colored.WHITELIGHT}Warning! The browser is about to open for vault OIDC login, "
        "close the tab once the sign-in is done!"
    )
    if _vault_command(command="vault login -method=oidc").returncode == 0:
        _vault_command(command="vault token renew -i 10h")
        print(f"{Colored.GREEN}Success! Vault OIDC Logged-In and extended for 10 hours!")
    # Fetching token
    token = _vault_command("vault token lookup --format json").stdout
    token = json.loads(str(token.decode('UTF-8')))['data']['id']
    # Setting new token in env file
    envdata = re.sub('.*VAULT_TOKEN_FOR_DYNACONF=.*', f"VAULT_TOKEN_FOR_DYNACONF={token}", envdata)
    with open(root_path, 'w') as envfile:
        envfile.write(envdata)
    print(
        f"{Colored.GREEN}Success! New OIDC token added to .env file to access secrets from vault!"
    )


def _vault_logout(root_path, envdata):
    # Teardown - Setting dymmy token in env file
    envdata = re.sub('.*VAULT_TOKEN_FOR_DYNACONF=.*', "# VAULT_TOKEN_FOR_DYNACONF=myroot", envdata)
    with open(root_path, 'w') as envfile:
        envfile.write(envdata)
    _vault_command('vault token revoke -self')
    print(f"{Colored.GREEN}Success! OIDC token removed from Env file successfully!")


def _vault_status():
    vstatus = _vault_command('vault token lookup')
    if vstatus.returncode == 0:
        print(str(vstatus.stdout.decode('UTF-8')))


if __name__ == '__main__':
    root_path = Path('.env')
    envdata = root_path.read_text()
    export_vault_env_vars(envdata=envdata)
    if sys.argv[-1] == '--login':
        _vault_login(root_path, envdata)
    elif sys.argv[-1] == '--status':
        _vault_status()
    else:
        _vault_logout(root_path, envdata)
    # Unsetting VAULT URL
    del os.environ['VAULT_ADDR']
