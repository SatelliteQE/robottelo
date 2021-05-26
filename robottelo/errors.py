"""Custom Errors for Robottelo"""


class GCECertNotFoundError(Exception):
    """An exception to raise when GCE Cert json is not available for creating GCE CR"""


class TemplateNotFoundError(Exception):
    """An exception to raise when Template is not available in Satellite"""


class ImproperlyConfigured(Exception):
    """Indicates that Robottelo somehow is improperly configured.

    For example, if settings file can not be found or some required
    configuration is not defined.
    """
