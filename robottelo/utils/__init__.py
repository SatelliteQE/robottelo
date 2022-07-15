# General utility functions which does not fit into other util modules OR
# Independent utility functions that doesnt need separate module
import os
import re
from pathlib import Path

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

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


def gen_ssh_keypairs():
    """Generates private SSH key with its public key"""
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    private = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    )
    public = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )
    return private.decode('utf-8'), public.decode('utf-8')
