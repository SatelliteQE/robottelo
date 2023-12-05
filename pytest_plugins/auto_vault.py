"""Plugin enables pytest to notify and update the requirements"""

from robottelo.utils.vault import Vault


def pytest_addoption(parser):
    """Options to allow user to update the requirements"""
    with Vault() as vclient:
        vclient.login()
