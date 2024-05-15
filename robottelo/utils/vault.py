"""Hashicorp Vault Utils where vault CLI is wrapped to perform vault operations"""

import json
import os
import re
import subprocess
import sys

from robottelo.exceptions import InvalidVaultURLForOIDC
from robottelo.logging import logger, robottelo_root_dir


class Vault:
    HELP_TEXT = (
        "Vault CLI in not installed in your system, "
        "refer link https://learn.hashicorp.com/tutorials/vault/getting-started-install to "
        "install vault CLI as per your system spec!"
    )

    def __init__(self, env_file='.env'):
        self.env_path = robottelo_root_dir.joinpath(env_file)
        self.envdata = None
        self.vault_enabled = None

    def setup(self):
        if self.env_path.exists():
            self.envdata = self.env_path.read_text()
            is_enabled = re.findall('^(?:.*\n)*VAULT_ENABLED_FOR_DYNACONF=(.*)', self.envdata)
            if is_enabled:
                self.vault_enabled = is_enabled[0]
            self.export_vault_addr()

    def teardown(self):
        if os.environ.get('VAULT_ADDR') is not None:
            del os.environ['VAULT_ADDR']

    def export_vault_addr(self):
        vaulturl = re.findall('VAULT_URL_FOR_DYNACONF=(.*)', self.envdata)[0]

        # Set Vault CLI Env Var
        os.environ['VAULT_ADDR'] = vaulturl

        # Dynaconf Vault Env Vars
        if (
            self.vault_enabled
            and self.vault_enabled in ['True', 'true']
            and 'localhost:8200' in vaulturl
        ):
            raise InvalidVaultURLForOIDC(
                f"{vaulturl} doesn't support OIDC login,"
                "please change url to corp vault in env file!"
            )

    def exec_vault_command(self, command: str, **kwargs):
        """A wrapper to execute the vault CLI commands

        :param comamnd str: The vault CLI command
        :param kwargs dict: Arguments to the subprocess run command to customize the run behavior
        """
        vcommand = subprocess.run(command, shell=True, capture_output=True, **kwargs)
        if vcommand.returncode != 0:
            verror = str(vcommand.stderr)
            if vcommand.returncode == 127:
                logger.error(f"Error! {self.HELP_TEXT}")
                sys.exit(1)
            if vcommand.stderr:
                if 'no such host' in verror:
                    logger.error("The Vault host is not reachable, check network availability.")
                    sys.exit()
                elif 'Error revoking token' in verror:
                    logger.info("Token is alredy revoked!")
                elif 'Error looking up token' in verror:
                    logger.info("Vault is not logged in!")
                else:
                    logger.error(f"Error! {verror}")
        return vcommand

    def login(self, **kwargs):
        if (
            self.vault_enabled
            and self.vault_enabled in ['True', 'true']
            and 'VAULT_SECRET_ID_FOR_DYNACONF' not in os.environ
            and self.status(**kwargs).returncode != 0
        ):
            logger.info(
                "Warning! The browser is about to open for vault OIDC login, "
                "close the tab once the sign-in is done!"
            )
            if (
                self.exec_vault_command(command="vault login -method=oidc", **kwargs).returncode
                == 0
            ):
                self.exec_vault_command(command="vault token renew -i 10h", **kwargs)
                logger.info("Success! Vault OIDC Logged-In and extended for 10 hours!")
            # Fetching tokens
            token = self.exec_vault_command("vault token lookup --format json").stdout
            token = json.loads(str(token.decode('UTF-8')))['data']['id']
            # Setting new token in env file
            _envdata = re.sub(
                '.*VAULT_TOKEN_FOR_DYNACONF=.*',
                f"VAULT_TOKEN_FOR_DYNACONF={token}",
                self.envdata,
            )
            self.env_path.write_text(_envdata)
            logger.info("Success! New OIDC token added to .env file to access secrets from vault!")

    def logout(self):
        # Teardown - Setting dymmy token in env file
        _envdata = re.sub(
            '.*VAULT_TOKEN_FOR_DYNACONF=.*', "# VAULT_TOKEN_FOR_DYNACONF=myroot", self.envdata
        )
        self.env_path.write_text(_envdata)
        vstatus = self.exec_vault_command('vault token revoke -self')
        if vstatus.returncode == 0:
            logger.info("Success! OIDC token removed from Env file successfully!")

    def status(self, **kwargs):
        vstatus = self.exec_vault_command('vault token lookup', **kwargs)
        if vstatus.returncode == 0:
            logger.info(str(vstatus.stdout.decode('UTF-8')))
        return vstatus

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()
