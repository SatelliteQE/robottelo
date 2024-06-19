# General utility functions which does not fit into other util modules OR
# Independent utility functions that doesnt need separate module
import base64
import re

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa


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


def validate_ssh_pub_key(key):
    """Validates if a string is in valid ssh pub key format
    :param key: A string containing a ssh public key encoded in base64
    :return: Boolean
    """

    if not isinstance(key, str):
        raise ValueError(f"Key should be a string type, received: {type(key)}")

    # 1) a valid pub key has 3 parts separated by space
    # 2) The second part (key string) should be a valid base64
    try:
        key_type, key_string, _ = key.split()  # need more than one value to unpack
        base64.decodebytes(key_string.encode('ascii'))
        return key_type in ('ecdsa-sha2-nistp256', 'ssh-dss', 'ssh-rsa', 'ssh-ed25519')
    except (ValueError, base64.binascii.Error):
        return False


def slugify_component(string, keep_hyphens=True):
    """Make component name a slug
       Arguments:
        string {str} -- Component name e.g: ActivationKeys
        keep_hyphens {bool} -- Keep hyphens or replace with underscores
    return:
        str -- component slug e.g: activationkeys
    """
    string = string.replace(" and ", "&")
    if not keep_hyphens:
        string = string.replace('-', '_')
    return re.sub("[^-_a-zA-Z0-9]", "", string.lower())


def parse_comma_separated_list(option_value):
    """Mainly used for parsing pytest option values."""
    if isinstance(option_value, str):
        if option_value.lower() == 'true':
            return True
        if option_value.lower() == 'false':
            return False
        return [item.strip() for item in option_value.split(',')]
    return None
