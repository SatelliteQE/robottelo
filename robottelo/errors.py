# -*- encoding: utf-8 -*-
"""Custom Errors for Robottelo"""


class GCECertNotFoundError(Exception):
    """An exception to raise when GCE Cert json is not available for creating GCE CR"""
