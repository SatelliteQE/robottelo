#!/usr/bin/env python
# This Enables and Disables individuals OIDC token to access secrets from vault
import json
import os
import re
import subprocess
import sys
import time

from robottelo.errors import InvalidVaultURLForOIDC

HELP_TEXT = (
    "Vault CLI in not installed in your system, "
    "refer link https://learn.hashicorp.com/tutorials/vault/getting-started-install to "
    "install vault CLI as per your system spec!"
)

# Color Codes
YELLOW = '\033[1;33m'
REDL = '\033[3;31m'
REDD = '\033[1;31m'
GREEN = '\033[1;32m'
WHITEL = '\033[1;30m'


def _load_env():
    print("\nFetching vault data from .env file and Exporting vault URL .....\n")
    ROOT_PATH = os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir)
    )
    with open(ROOT_PATH + '/.env') as envfile:
        envdata = envfile.read()
    return ROOT_PATH, envdata


def _export_vault_url(envdata):
    vaulturl = re.findall('VAULT_URL_FOR_DYNACONF=(.*)', envdata)[0]
    if 'localhost:8200' in vaulturl:
        raise InvalidVaultURLForOIDC(
            f"{REDL}{vaulturl} doesnt supports OIDC login,"
            "please change url to corp vault in env file!"
        )
    os.environ['VAULT_ADDR'] = vaulturl


def _vault_command(command: str):
    vcommand = subprocess.run(command, capture_output=True, shell=True)
    if vcommand.returncode != 0:
        verror = str(vcommand.stderr)
        if 'vault: command not found' in verror:
            print(f"{REDD}Error! {HELP_TEXT}")
            sys.exit(1)
        elif 'Error revoking token' in verror:
            print(f"{GREEN}Token is alredy revoked!")
            sys.exit(0)
        elif 'Error looking up token' in verror:
            print(f"{YELLOW}Warning! Vault not logged in, please run 'make vault-login'!")
            sys.exit(2)
        else:
            print(f"{REDD}Error! {verror}")
            sys.exit(1)
    return vcommand


def _vault_login(root_path, envdata):
    print(
        f"{WHITEL}Warning! The browser is about to open for vault OIDC login, "
        "close the tab once the sign in is done!"
    )
    time.sleep(5)
    if _vault_command(command="vault login -method=oidc").returncode == 0:
        _vault_command(command="vault token renew -i 10h")
        print(f"{GREEN}Success! Vault OIDC Logged-In and extended for 10 hours!")
    # Fetching token
    token = _vault_command("vault token lookup --format json").stdout
    token = json.loads(str(token.decode('UTF-8')))['data']['id']
    # Setting new token in env file
    envdata = re.sub('.*VAULT_TOKEN_FOR_DYNACONF=.*', f"VAULT_TOKEN_FOR_DYNACONF={token}", envdata)
    with open(root_path + '/.env', 'w') as envfile:
        envfile.write(envdata)
    print(f"{GREEN}Success! New OIDC token is added to .env file to access secrets from vault!")


def _vault_logout(root_path, envdata):
    # Teardown - Setting dymmy token in env file
    envdata = re.sub('.*VAULT_TOKEN_FOR_DYNACONF=.*', "# VAULT_TOKEN_FOR_DYNACONF=myroot", envdata)
    with open(root_path + '/.env', 'w') as envfile:
        envfile.write(envdata)
    _vault_command('vault token revoke -self')
    print(f"{GREEN}Success! OIDC token removed from Env file successfully!")


def _vault_status():
    vstatus = _vault_command('vault token lookup')
    if vstatus.returncode == 0:
        print(str(vstatus.stdout.decode('UTF-8')))


if __name__ == '__main__':
    root_path, envdata = _load_env()
    _export_vault_url(envdata)
    if sys.argv[-1] == '--login':
        _vault_login(root_path, envdata)
    elif sys.argv[-1] == '--status':
        _vault_status()
    else:
        _vault_logout(root_path, envdata)
    # Unsetting VAULT URL
    del os.environ['VAULT_ADDR']
