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


class InvalidVaultURLForOIDC(Exception):
    """Raised if the vault doesnt allows OIDC login"""


class RepositoryAlreadyDefinedError(Exception):
    """Raised when a repository has already a predefined key"""


class DistroNotSupportedError(Exception):
    """Raised when using a non supported distro"""


class RepositoryDataNotFound(Exception):
    """Raised when repository data cannot be found for a predefined distro"""


class OnlyOneOSRepositoryAllowed(Exception):
    """Raised when trying to more than one OS repository to a collection"""


class RepositoryAlreadyCreated(Exception):
    """Raised when a repository content is already created and trying to launch
    the create an other time"""


class ReposContentSetupWasNotPerformed(Exception):
    """Raised when trying to setup a VM but the repositories content was not
    setup"""


class DataFileError(Exception):
    """Indicates any issue when reading a data file."""


class HostPingFailed(Exception):
    """Indicates any issue when provisioning a host."""


class InvalidArgumentError(Exception):
    """Indicates an error when an invalid argument is received."""


class ProxyError(Exception):
    """Indicates an error in state of proxy"""


class DownloadFileError(Exception):
    """Indicates an error when failure in downloading file from server."""
