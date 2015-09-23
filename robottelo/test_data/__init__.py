"""Provides functions to get the path of read a test data file."""
import os

OS_TEMPLATE = 'os_template.txt'
PARTITION_SCRIPT = 'partition_script.txt'
PUPPET_MODULE_NTP_PUPPETLABS = 'puppetlabs-ntp-3.2.1.tar.gz'
SNIPPET = 'snippet.txt'
VALID_GPG_KEY = 'valid_gpg_key.txt'
VALID_GPG_KEY_BETA = 'valid_gpg_key_beta.txt'
WHICH_RPM = 'which-2.19-6.el6.x86_64.rpm'
ZOO_CUSTOM_GPG_KEY = 'zoo_custom_gpgkey.txt'

_BASE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


class DataFileError(Exception):
    """Indicates any issue when reading a data file."""


def path(data_file):
    """Return the path of a test data file."""
    data_path = os.path.join(_BASE_PATH, data_file)
    if not os.path.isfile(data_path):
        raise DataFileError(
            'Could not locate the data file {}'.format(data_file))
    return data_path


def read(data_file):
    """Read and return the content of a test data file."""
    with open(path(data_file)) as handler:
        return handler.read()
