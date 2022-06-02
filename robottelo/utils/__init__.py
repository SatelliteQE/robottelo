# General utility functions which does not fit into other util modules
import os
import re
from pathlib import Path

from robottelo.constants import Colored
from robottelo.errors import InvalidVaultURLForOIDC


def export_vault_env_vars(filename=None, envdata=None):
    if not envdata:
        envdata = Path(filename or '.env').read_text()
    vaulturl = re.findall('VAULT_URL_FOR_DYNACONF=(.*)', envdata)[0]

    # Vault CLI Env Var
    os.environ['VAULT_ADDR'] = vaulturl

    # Dynaconf Vault Env Vars
    if re.findall('VAULT_ENABLED_FOR_DYNACONF=(.*)', envdata)[0] == 'true':
        if 'localhost:8200' in vaulturl:
            raise InvalidVaultURLForOIDC(
                f"{Colored.REDDARK}{vaulturl} doesnt supports OIDC login,"
                "please change url to corp vault in env file!"
            )
