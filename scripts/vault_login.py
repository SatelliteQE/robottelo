#!/usr/bin/env python
# This Enables and Disables individuals OIDC token to access secrets from vault
import sys

from robottelo.utils.vault import Vault


if __name__ == '__main__':
    with Vault() as vclient:
        if sys.argv[-1] == '--login':
            vclient.login()
        elif sys.argv[-1] == '--status':
            vclient.status()
        else:
            vclient.logout()
