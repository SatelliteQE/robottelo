"""Several helper methods and functions."""
from urllib.parse import urljoin  # noqa

from nailgun.config import ServerConfig

from robottelo.config import get_credentials
from robottelo.config import get_url


def get_nailgun_config(user=None):
    """Return a NailGun configuration file constructed from default values.

    :param user: The ```nailgun.entities.User``` object of an user with additional passwd
        property/attribute

    :return: ``nailgun.config.ServerConfig`` object, populated from user parameter object else
        with values from ``robottelo.config.settings``

    """
    creds = (user.login, user.passwd) if user else get_credentials()
    return ServerConfig(get_url(), creds, verify=False)
