"""Define and instantiate the configuration class for virtwho hypervisors."""
import logging.config
import os
from configparser import ConfigParser
from configparser import NoOptionError
from configparser import NoSectionError

from robottelo.config import casts

LOGGER = logging.getLogger(__name__)
SETTINGS_FILE_NAME = 'virtwho.properties'


class ImproperlyConfigured(Exception):
    """Indicates that virtwho hypervisor somehow is improperly configured.

    For example, if settings file can not be found or some required
    configuration is not defined.
    """


def get_project_root():
    """Return the path to the Robottelo project root directory.

    :return: A directory path.
    :rtype: str
    """
    return os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class INIReader(object):
    """ConfigParser wrapper able to cast value when reading INI options."""

    # Helper casters
    cast_boolean = casts.Boolean()
    cast_dict = casts.Dict()
    cast_list = casts.List()
    cast_logging_level = casts.LoggingLevel()
    cast_tuple = casts.Tuple()
    cast_webdriver_desired_capabilities = casts.WebdriverDesiredCapabilities()

    def __init__(self, path):
        self.config_parser = ConfigParser()
        with open(path) as handler:
            self.config_parser.read_file(handler)

    def get(self, section, option, default=None, cast=None):
        """Read an option from a section of a INI file.

        First try to lookup for the value as an environment variable having the
        following format: ROBOTTELO_{SECTION}_{OPTION}.

        The default value will return if the look up option is not available.
        The value will be cast using a callable if specified otherwise a string
        will be returned.

        :param section: Section to look for.
        :param option: Option to look for.
        :param default: The value that should be used if the option is not
            defined.
        :param cast: If provided the value will be cast using the cast
            provided.
        """
        # First try to read from environment variable.
        # [bugzilla]
        # api_key=123456
        # can be expressed as:
        # $ export ROBOTTELO_BUGZILLA_API_KEY=123456
        value = os.environ.get(f'ROBOTTELO_{section.upper()}_{option.upper()}')

        try:
            # If envvar does not exist then try from .properties file.
            value = value or self.config_parser.get(section, option)
            if cast is not None:
                if cast is bool:
                    value = self.cast_boolean(value)
                elif cast is dict:
                    value = self.cast_dict(value)
                elif cast is list:
                    value = self.cast_list(value)
                elif cast is tuple:
                    value = self.cast_tuple(value)
                else:
                    value = cast(value)
        except (NoSectionError, NoOptionError):
            value = default
        return value

    def has_section(self, section):
        """Check if section is available."""
        return self.config_parser.has_section(section)


class FeatureSettings(object):
    """Settings related to a feature.

    Create a instance of this class and assign attributes to map to the feature
    options.
    """

    def read(self, reader):
        """Subclasses must implement this method in order to populate itself
        with expected settings values.

        :param reader: An INIReader instance to read the settings.
        """
        raise NotImplementedError('Subclasses must implement read method.')

    def validate(self):
        """Subclasses must implement this method in order to validade the
        settings and raise ``ImproperlyConfigured`` if any issue is found.
        """
        raise NotImplementedError('Subclasses must implement validate method.')


class SkuSettings(FeatureSettings):
    """Sku settings definitions"""

    def __init__(self, *args, **kwargs):
        super(SkuSettings, self).__init__(*args, **kwargs)
        # SKU Information
        self.vdc_physical = None
        self.vdc_virtual = None

    def read(self, reader):
        """Read sku settings."""
        # SKU Information
        self.vdc_physical = reader.get('sku', 'vdc_physical')
        self.vdc_virtual = reader.get('sku', 'vdc_virtual')

    def validate(self):
        """Validate sku settings."""
        validation_errors = []
        mandatory = (
            self.vdc_physical,
            self.vdc_virtual,
        )
        if not all(mandatory):
            validation_errors.append('vdc_physical, vdc_virtual options must be provided.')
        return validation_errors


class EsxSettings(FeatureSettings):
    """Esx settings definitions."""

    def __init__(self, *args, **kwargs):
        super(EsxSettings, self).__init__(*args, **kwargs)
        # Hypervisor Information
        self.hypervisor_type = None
        self.hypervisor_server = None
        self.hypervisor_username = None
        self.hypervisor_password = None
        self.guest = None
        self.guest_port = None
        self.guest_username = None
        self.guest_password = None

    def read(self, reader):
        """Read esx settings."""
        # Hypervisor Information
        self.hypervisor_type = reader.get('esx', 'hypervisor_type')
        self.hypervisor_server = reader.get('esx', 'hypervisor_server')
        self.hypervisor_username = reader.get('esx', 'hypervisor_username')
        self.hypervisor_password = reader.get('esx', 'hypervisor_password')
        self.guest = reader.get('esx', 'guest')
        self.guest_port = reader.get('esx', 'guest_port', 22, int)
        self.guest_username = reader.get('esx', 'guest_username')
        self.guest_password = reader.get('esx', 'guest_password')

    def validate(self):
        """Validate esx settings."""
        validation_errors = []
        mandatory = (
            self.hypervisor_type,
            self.hypervisor_server,
            self.hypervisor_username,
            self.hypervisor_password,
            self.guest,
            self.guest_username,
            self.guest_password,
        )
        if not all(mandatory):
            validation_errors.append(
                '[esx] hypervisor_type, hypervisor_server, hypervisor_username, '
                'hypervisor_password, guest , guest_username, guest_password '
                'options must be provided.'
            )
        return validation_errors


class XenSettings(FeatureSettings):
    """Xen settings definitions."""

    def __init__(self, *args, **kwargs):
        super(XenSettings, self).__init__(*args, **kwargs)
        # Hypervisor Information
        self.hypervisor_type = None
        self.hypervisor_server = None
        self.hypervisor_username = None
        self.hypervisor_password = None
        self.guest = None
        self.guest_port = None
        self.guest_username = None
        self.guest_password = None

    def read(self, reader):
        """Read xen settings."""
        # Hypervisor Information
        self.hypervisor_type = reader.get('xen', 'hypervisor_type')
        self.hypervisor_server = reader.get('xen', 'hypervisor_server')
        self.hypervisor_username = reader.get('xen', 'hypervisor_username')
        self.hypervisor_password = reader.get('xen', 'hypervisor_password')
        self.guest = reader.get('xen', 'guest')
        self.guest_port = reader.get('xen', 'guest_port', 22, int)
        self.guest_username = reader.get('xen', 'guest_username')
        self.guest_password = reader.get('xen', 'guest_password')

    def validate(self):
        """Validate xen settings."""
        validation_errors = []
        mandatory = (
            self.hypervisor_type,
            self.hypervisor_server,
            self.hypervisor_username,
            self.hypervisor_password,
            self.guest,
            self.guest_username,
            self.guest_password,
        )
        if not all(mandatory):
            validation_errors.append(
                '[xen] hypervisor_type, hypervisor_server, hypervisor_username, '
                'hypervisor_password, guest , guest_username, guest_password '
                'options must be provided.'
            )
        return validation_errors


class HypervSettings(FeatureSettings):
    """Hyperv settings definitions."""

    def __init__(self, *args, **kwargs):
        super(HypervSettings, self).__init__(*args, **kwargs)
        # Hypervisor Information
        self.hypervisor_type = None
        self.hypervisor_server = None
        self.hypervisor_username = None
        self.hypervisor_password = None
        self.guest = None
        self.guest_port = None
        self.guest_username = None
        self.guest_password = None

    def read(self, reader):
        """Read hyperv settings."""
        # Hypervisor Information
        self.hypervisor_type = reader.get('hyperv', 'hypervisor_type')
        self.hypervisor_server = reader.get('hyperv', 'hypervisor_server')
        self.hypervisor_username = reader.get('hyperv', 'hypervisor_username')
        self.hypervisor_password = reader.get('hyperv', 'hypervisor_password')
        self.guest = reader.get('hyperv', 'guest')
        self.guest_port = reader.get('hyperv', 'guest_port', 22, int)
        self.guest_username = reader.get('hyperv', 'guest_username')
        self.guest_password = reader.get('hyperv', 'guest_password')

    def validate(self):
        """Validate hyperv settings."""
        validation_errors = []
        mandatory = (
            self.hypervisor_type,
            self.hypervisor_server,
            self.hypervisor_username,
            self.hypervisor_password,
            self.guest,
            self.guest_username,
            self.guest_password,
        )
        if not all(mandatory):
            validation_errors.append(
                '[hyperv] hypervisor_type, hypervisor_server, hypervisor_username, '
                'hypervisor_password, guest , guest_username, guest_password '
                'options must be provided.'
            )
        return validation_errors


class RhevmSettings(FeatureSettings):
    """Rhevm settings definitions."""

    def __init__(self, *args, **kwargs):
        super(RhevmSettings, self).__init__(*args, **kwargs)
        # Hypervisor Information
        self.hypervisor_type = None
        self.hypervisor_server = None
        self.hypervisor_username = None
        self.hypervisor_password = None
        self.guest = None
        self.guest_port = None
        self.guest_username = None
        self.guest_password = None

    def read(self, reader):
        """Read rhevm settings."""
        # Hypervisor Information
        self.hypervisor_type = reader.get('rhevm', 'hypervisor_type')
        self.hypervisor_server = reader.get('rhevm', 'hypervisor_server')
        self.hypervisor_username = reader.get('rhevm', 'hypervisor_username')
        self.hypervisor_password = reader.get('rhevm', 'hypervisor_password')
        self.guest = reader.get('rhevm', 'guest')
        self.guest_port = reader.get('rhevm', 'guest_port', 22, int)
        self.guest_username = reader.get('rhevm', 'guest_username')
        self.guest_password = reader.get('rhevm', 'guest_password')

    def validate(self):
        """Validate rhevm settings."""
        validation_errors = []
        mandatory = (
            self.hypervisor_type,
            self.hypervisor_server,
            self.hypervisor_username,
            self.hypervisor_password,
            self.guest,
            self.guest_username,
            self.guest_password,
        )
        if not all(mandatory):
            validation_errors.append(
                '[rhevm] hypervisor_type, hypervisor_server, hypervisor_username, '
                'hypervisor_password, guest , guest_username, guest_password '
                'options must be provided.'
            )
        return validation_errors


class LibvirtSettings(FeatureSettings):
    """Libvirt settings definitions."""

    def __init__(self, *args, **kwargs):
        super(LibvirtSettings, self).__init__(*args, **kwargs)
        # Hypervisor Information
        self.hypervisor_type = None
        self.hypervisor_server = None
        self.hypervisor_username = None
        self.guest = None
        self.guest_port = None
        self.guest_username = None
        self.guest_password = None

    def read(self, reader):
        """Read libvirt settings."""
        # Hypervisor Information
        self.hypervisor_type = reader.get('libvirt', 'hypervisor_type')
        self.hypervisor_server = reader.get('libvirt', 'hypervisor_server')
        self.hypervisor_username = reader.get('libvirt', 'hypervisor_username')
        self.guest = reader.get('libvirt', 'guest')
        self.guest_port = reader.get('libvirt', 'guest_port', 22, int)
        self.guest_username = reader.get('libvirt', 'guest_username')
        self.guest_password = reader.get('libvirt', 'guest_password')

    def validate(self):
        """Validate libvirt settings."""
        validation_errors = []
        mandatory = (
            self.hypervisor_type,
            self.hypervisor_server,
            self.hypervisor_username,
            self.guest,
            self.guest_username,
            self.guest_password,
        )
        if not all(mandatory):
            validation_errors.append(
                '[libvirt] hypervisor_type, hypervisor_server, hypervisor_username, '
                'guest , guest_username, guest_password options must be provided.'
            )
        return validation_errors


class KubevirtSettings(FeatureSettings):
    """Kubevirt settings definitions."""

    def __init__(self, *args, **kwargs):
        super(KubevirtSettings, self).__init__(*args, **kwargs)
        # Hypervisor Information
        self.hypervisor_type = None
        self.hypervisor_server = None
        self.hypervisor_config_file = None
        self.guest = None
        self.guest_port = None
        self.guest_username = None
        self.guest_password = None

    def read(self, reader):
        """Read kubevirt settings."""
        # Hypervisor Information
        self.hypervisor_type = reader.get('kubevirt', 'hypervisor_type')
        self.hypervisor_server = reader.get('kubevirt', 'hypervisor_server')
        self.hypervisor_config_file = reader.get('kubevirt', 'hypervisor_config_file')
        self.guest = reader.get('kubevirt', 'guest')
        self.guest_port = reader.get('kubevirt', 'guest_port', 22, int)
        self.guest_username = reader.get('kubevirt', 'guest_username')
        self.guest_password = reader.get('kubevirt', 'guest_password')

    def validate(self):
        """Validate kubevirt settings."""
        validation_errors = []
        mandatory = (
            self.hypervisor_type,
            self.hypervisor_server,
            self.hypervisor_config_file,
            self.guest,
            self.guest_username,
            self.guest_password,
        )
        if not all(mandatory):
            validation_errors.append(
                '[kubevirt] hypervisor_type, hypervisor_server, hypervisor_password, '
                'hypervisor_config_file, guest , guest_username, '
                'guest_password options must be provided.'
            )
        return validation_errors


class VirtwhoSettings(object):
    """Virtwho's settings representation."""

    def __init__(self):
        self._validation_errors = []
        self.hypervisor = None
        self.esx = EsxSettings()
        self.xen = XenSettings()
        self.hyperv = HypervSettings()
        self.rhevm = RhevmSettings()
        self.libvirt = LibvirtSettings()
        self.kubevirt = KubevirtSettings()
        self.sku = SkuSettings()

    def configure(self, settings_path=None):
        """Read the settings file and parse the configuration.

        :param str settings_path: path to settings file to read. If None, looks in the project
            root for a file named 'robottelo.properties'.

        :raises: ImproperlyConfigured if any issue is found during the parsing
            or validation of the configuration.
        """

        if not settings_path:
            # Expect the settings file to be on the robottelo project root.
            settings_path = os.path.join(get_project_root(), SETTINGS_FILE_NAME)

        if not os.path.isfile(settings_path):
            raise ImproperlyConfigured(
                'Not able to find settings file at {}'.format(settings_path)
            )

        self.reader = INIReader(settings_path)
        attrs = map(lambda attr_name: (attr_name, getattr(self, attr_name)), dir(self))
        feature_settings = filter(lambda tpl: isinstance(tpl[1], FeatureSettings), attrs)
        for name, settings in feature_settings:
            settings.read(self.reader)
            # Only has section will extend the error
            if self.reader.has_section(name):
                self._validation_errors.extend(settings.validate())
        if self._validation_errors:
            raise ImproperlyConfigured(
                'Failed to validate the configuration, check the message(s):\n'
                '{}'.format('\n'.join(self._validation_errors))
            )
