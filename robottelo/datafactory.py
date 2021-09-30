"""Data Factory for all entities"""
import random
import string
from functools import wraps
from urllib.parse import quote_plus

from fauxfactory import gen_alpha
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url
from fauxfactory import gen_utf8

from robottelo.config import settings
from robottelo.constants import DOMAIN
from robottelo.constants import STRING_TYPES


class InvalidArgumentError(Exception):
    """Indicates an error when an invalid argument is received."""


def filtered_datapoint(func):
    """Overrides the data creator functions in this class to return 1 value and
    transforms data dictionary to pytest's parametrize acceptable format for
    new style generators.

    If run_one_datapoint=false, return the entire data set. (default: False)
    If run_one_datapoint=true, return a random data.

    """
    if not settings.configured:
        settings.configure()

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        """Perform smoke test attribute check"""
        dataset = func(*args, **kwargs)
        if isinstance(dataset, dict):
            # New UI tests are written using pytest, update dict to support pytest's parametrize
            if (
                'ui' in args
                or kwargs.get('interface') == 'ui'
                and settings.ui.webdriver == 'chrome'
            ):
                # Chromedriver only supports BMP chars
                utf8 = dataset.pop('utf8', None)
                if utf8:
                    dataset['utf8'] = gen_utf8(len(utf8), smp=False)
            if settings.robottelo.run_one_datapoint:
                key = random.choice(list(dataset.keys()))
                dataset = {key: dataset[key]}
        else:
            # Otherwise use list for backwards compatibility
            dataset = list(dataset)
            if settings.robottelo.run_one_datapoint:
                dataset = [random.choice(dataset)]
        return dataset

    return func_wrapper


def parametrized(data):
    """Transforms data dictionary to pytest's parametrize acceptable format.
    Generates parametrized test names from data dict keys.

    :param dict data: dictionary with parametrized test names as dict keys and
        parametrized arguments as dict values
    """
    if isinstance(data, dict):
        return {
            'ids': list(data.keys()),
            'argvalues': list(data.values()),
        }
    else:
        return {
            'ids': [str(i) for i in range(len(data))],
            'argvalues': list(data),
        }


@filtered_datapoint
def generate_strings_list(length=None, exclude_types=None, min_length=3, max_length=30):
    """Generates a list of different input strings.

    :param int length: Specifies the length of the strings to be
        be generated. If the len1 is None then the list is
        returned with string types of random length.
    :param exclude_types: Specify a list of data types to be removed from
        generated list. example: exclude_types=['html', 'cjk']
    :param int min_length: Minimum length to be used in integer generator
    :param int max_length: Maximum length to be used in integer generator
    :returns: A list of various string types.

    """
    if length is None:
        length = gen_integer(min_length, max_length)

    strings = {str_type: gen_string(str_type, length) for str_type in STRING_TYPES}

    # Handle No bug_id, If some entity doesn't support a str_type.
    # Remove str_type from dictionary only if bug is open.
    if exclude_types:
        for item in exclude_types:
            strings.pop(item, None)

    return list(strings.values())


def add_uppercase_char_into_string(text=None, length=10):
    """Fix string to include a minimum of one uppercase character.
    https://github.com/SatelliteQE/robottelo/issues/4742

    :param str text: String to include uppercase character.
    :param int length: Length of string that we create in case string to change
        was not provided.
    """
    if text is None:
        text = gen_string('alpha', length)
    st_chars = list(text)
    st_chars[random.randint(0, len(st_chars) - 1)] = random.choice(string.ascii_uppercase)
    return ''.join(st_chars)


@filtered_datapoint
def invalid_emails_list():
    """
    Returns a list of invalid emails.

    Based on RFC 5321 and 5322, however consecutive dots are removed from
    the list, as such emails, e.g. `email@example..c` or `dot..dot@example.com`
    are common on the wild and it was decided to treat them as valid.

    For more information, see `Bugzilla #1455501:
    <https://bugzilla.redhat.com/show_bug.cgi?id=1455501>`_.
    """
    return [
        'foreman@',
        '@foreman',
        '@',
        'Abc.example.com',
        'A@b@c@example.com',
        # total length 255:
        f'{gen_string("alpha", 243)}@example.com',
        f'{gen_string("html")}@example.com',
        's p a c e s@example.com',
    ]


@filtered_datapoint
def invalid_boolean_strings(list_len=10):
    """Create a list of invalid booleans. E.g not true nor false

    :param list_len: len of the list to be generated
    :return: list
    """

    def not_boolean_str(s):
        return s not in ('true', 'false')

    return [gen_alpha(validator=not_boolean_str, default='notboolean') for _ in range(list_len)]


def xdist_adapter(argvalues):
    """Adapter to avoid error when running tests on xdist
    Check https://github.com/pytest-dev/pytest-xdist/issues/149

    It returns a dict with lst as argvalues and range(len(lst)) as ids

    Since every run has the same number of values, ids is going to be the same
    on different workers.

    .. code-block:: python

        dct = xdist_adapter(invalid_boolean_strings())

        @pytest.mark.parametrize('value', **dct)
        def test_something(value):
        #some code here

    :param argvalues: to be passed to parametrize
    :return: dict
    """
    return {'argvalues': argvalues, 'ids': [str(index) for index in range(len(argvalues))]}


@filtered_datapoint
def invalid_id_list():
    """Generates a list of invalid IDs."""
    return [gen_string('alpha'), None, '', -1]


@filtered_datapoint
def invalid_names_list():
    """Generates a list of invalid names."""
    return generate_strings_list(300)


@filtered_datapoint
def valid_domain_names(interface=None, length=None):
    """Valid domain names."""
    max_len = 255 - len(DOMAIN % '')
    if not length:
        length = random.randint(1, max_len)
    if length > max_len:
        raise ValueError(f'length is too large, max: {max_len}')
    names = {
        'alphanumeric': DOMAIN % gen_string('alphanumeric', length),
        'alpha': DOMAIN % gen_string('alpha', length),
        'numeric': DOMAIN % gen_string('numeric', length),
        'latin1': DOMAIN % gen_string('latin1', length),
        'utf8': DOMAIN % gen_utf8(length),
    }
    return names


@filtered_datapoint
def invalid_domain_names(interface=None):
    """Invalid domain names."""
    return {
        'empty': '\0',
        'whitespace': ' ',
        'tab': '\t',
        'toolong': gen_string('alphanumeric', 300),
    }


@filtered_datapoint
def invalid_usernames_list():
    return [
        '',
        'space {gen_string("alpha")}',
        gen_string('alpha', 101),
        gen_string('html'),
    ]


@filtered_datapoint
def invalid_values_list(interface=None):
    """Generates a list of invalid input values.

    This returns invalid values from :meth:`invalid_names_list` and some
    interface (api/cli/ui) specific empty string values.

    :param str interface: Interface name (one of api/cli/ui).
    :return: Returns the invalid values list
    :raises: :meth:`InvalidArgumentError`: If an invalid interface is received.

    """
    if interface not in ['api', 'cli', 'ui', None]:
        raise InvalidArgumentError('Valid interface values are api, cli, ui only')
    if interface == 'ui':
        return ['', ' '] + invalid_names_list()
    else:  # interface = api or cli or None
        return ['', ' ', '\t'] + invalid_names_list()


@filtered_datapoint
def valid_data_list(interface=None):
    """Generates a list of valid input values.

    Note:
    Although this helper is widely used for different attributes for several
    entities, the following are known behaviors and are handled specifically in
    the corresponding test modules::

        Org - name max length is 242
        Loc - name max length is 246

    """
    return {
        'alpha': gen_string('alpha', random.randint(1, 255)),
        'numeric': gen_string('numeric', random.randint(1, 255)),
        'alphanumeric': gen_string('alphanumeric', random.randint(1, 255)),
        'latin1': gen_string('latin1', random.randint(1, 255)),
        'utf8': gen_string('utf8', random.randint(1, 85)),
        'cjk': gen_string('cjk', random.randint(1, 85)),
        'html': gen_string('html', random.randint(1, 85)),
    }


@filtered_datapoint
def valid_docker_repository_names():
    """Generates a list of valid names for Docker repository."""
    names = [
        gen_string('alphanumeric', random.randint(1, 255)),
        gen_string('alpha', random.randint(1, 255)),
        gen_string('cjk', random.randint(1, 85)),
        gen_string('latin1', random.randint(1, 255)),
        gen_string('numeric', random.randint(1, 255)),
        gen_string('utf8', random.randint(1, 85)),
        gen_string('html', random.randint(1, 85)),
    ]
    return names


@filtered_datapoint
def valid_emails_list():
    """Returns a list of valid emails."""
    return [
        f'{gen_string("alpha")}@example.com',
        f'{gen_string("alphanumeric")}@example.com',
        f'{gen_string("numeric")}@example.com',
        f'{gen_string("alphanumeric", 48)}@example.com',
        f'{gen_string("alphanumeric")}+{gen_string("alphanumeric")}@example.com',
        f'{gen_string("alphanumeric")}.{gen_string("alphanumeric")}@example.com',
        '"():;"@example.com',
        '!#$%&*+-/=?^`{|}~@example.com',
    ]


@filtered_datapoint
def valid_environments_list():
    """Returns a list of valid environment names"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
        gen_string('alphanumeric', 255),
    ]


@filtered_datapoint
def invalid_environments_list():
    """Returns a list of invalid environment names"""
    return [
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('cjk'),
        gen_string('html'),
    ]


@filtered_datapoint
def valid_hosts_list(domain_length=10):
    """Generates a list of valid host names.

    Note::
    Host name format stored in db is 'fqdn=' + host_name + '.' + domain_name
    Host name max length is: 255 - 'fqdn=' - '.' - domain name length
    (default is 10) = 239 chars (by default). Name should be transformed into
    lower case

    :param int domain_length: Domain name length (default is 10).
    :return: Returns the valid host names list
    """
    return [
        gen_string('alphanumeric', random.randint(1, (255 - 6 - domain_length))).lower(),
        gen_string('alpha', random.randint(1, (255 - 6 - domain_length))).lower(),
        gen_string('numeric', random.randint(1, (255 - 6 - domain_length))),
    ]


@filtered_datapoint
def valid_hostgroups_list():
    """Generates a list of valid host group names.

    Note::
    Host group name max length is 245 chars.
    220 chars for html as the largest html tag in fauxfactory is 10 chars long,
    so 245 - (10 chars + 10 chars + '<></>' chars) = 220 chars.

    :return: Returns the valid host group names list
    """
    return [
        gen_string('alphanumeric', random.randint(1, 245)),
        gen_string('alpha', random.randint(1, 245)),
        gen_string('cjk', random.randint(1, 245)),
        gen_string('latin1', random.randint(1, 245)),
        gen_string('numeric', random.randint(1, 245)),
        gen_string('utf8', random.randint(1, 245)),
        gen_string('html', random.randint(1, 220)),
    ]


@filtered_datapoint
def valid_labels_list():
    """Generates a list of valid labels."""
    return [
        gen_string('alphanumeric', random.randint(1, 128)),
        gen_string('alpha', random.randint(1, 128)),
    ]


@filtered_datapoint
def valid_names_list():
    """Generates a list of valid names."""
    return [
        gen_string('utf8', 5),
        gen_string('utf8', 255),
        f"{gen_string('utf8', 4)}-{gen_string('utf8', 4)}",
        f"{gen_string('utf8', 4)}.{gen_string('utf8', 4)}",
        f"նոր օգտվող-{gen_string('utf8', 2)}",
        f"新用戶-{gen_string('utf8', 2)}",
        f"नए उपयोगकर्ता-{gen_string('utf8', 2)}",
        f"нового пользователя-{gen_string('utf8', 2)}",
        f"uusi käyttäjä-{gen_string('utf8', 2)}",
        f"νέος χρήστης-{gen_string('utf8', 2)}",
        f"foo@!#$^&*( ) {gen_string('utf8')}",
        f"<blink>{gen_string('utf8')}</blink>",
        f"bar+{{}}|\"?hi {gen_string('utf8')}",
        f" {gen_string('utf8')}",
        f"{gen_string('utf8')} ",
    ]


@filtered_datapoint
def valid_org_names_list():
    """Generates a list of valid organization names.

    Note::
    Organization name max length is 242 chars.
    217 chars for html as the largest html tag in fauxfactory is 10 chars long,
    so 242 - (10 chars + 10 chars + '<></>' chars) = 217 chars.

    :return: Returns the valid organization names list
    """
    return [
        gen_string('alphanumeric', random.randint(1, 242)),
        gen_string('alpha', random.randint(1, 242)),
        gen_string('cjk', random.randint(1, 242)),
        gen_string('latin1', random.randint(1, 242)),
        gen_string('numeric', random.randint(1, 242)),
        gen_string('utf8', random.randint(1, 80)),
        gen_string('html', random.randint(1, 217)),
    ]


@filtered_datapoint
def valid_usernames_list():
    """Returns a list of valid user names."""
    return generate_strings_list(exclude_types=['html'], min_length=1, max_length=50)


@filtered_datapoint
def valid_interfaces_list():
    """Generates a list of valid host interface names."""
    return [
        gen_string('alpha', random.randint(1, 255)).lower(),
        gen_string('alphanumeric', random.randint(1, 255)).lower(),
        gen_string('numeric', random.randint(1, 255)),
    ]


@filtered_datapoint
def invalid_interfaces_list():
    """Generates a list of invalid host interface names."""
    return [
        gen_string('alpha', 300).lower(),
        gen_string('alphanumeric', 300).lower(),
        gen_string('numeric', 300),
        gen_string('cjk'),
        gen_string('cyrillic'),
        gen_string('html'),
        gen_string('latin1'),
        gen_string('utf8'),
    ]


def valid_http_credentials(url_encoded=False):
    """Returns a list of valid credentials for HTTP authentication
    The credentials dictionary contains the following keys:
    login - a username
    pass - a password
    quote - a Bool flag stating whether the credentials include special chars
    http_valid - a Bool flag stating whether the HTTP authentication will pass
    successfully on the server

    :param url_encoded: flag for quoting special characters
    :return: A list of dictionaries with user and password credentials
    """
    credentials = [
        {'login': 'admin', 'pass': 'changeme', 'quote': False, 'http_valid': True},
        {'login': '@dmin', 'pass': 'changeme', 'quote': True, 'http_valid': True},
        {'login': 'adm/n', 'pass': 'changeme', 'quote': False, 'http_valid': True},
        {'login': 'admin2', 'pass': 'ch@ngeme', 'quote': True, 'http_valid': True},
        {'login': 'admin3', 'pass': 'chan:eme', 'quote': False, 'http_valid': True},
        {'login': 'admin4', 'pass': 'chan/eme', 'quote': True, 'http_valid': True},
        {'login': 'admin5', 'pass': 'ch@n:eme', 'quote': True, 'http_valid': True},
        {'login': '0', 'pass': 'mypassword', 'quote': False, 'http_valid': True},
        {
            'login': '0123456789012345678901234567890123456789',
            'pass': 'changeme',
            'quote': False,
            'http_valid': True,
        },
        {'login': 'admin', 'pass': '', 'quote': False, 'http_valid': False},
        {'login': '', 'pass': 'mypassword', 'quote': False, 'http_valid': False},
        {'login': '', 'pass': '', 'quote': False, 'http_valid': False},
        {
            'login': gen_string('alpha', gen_integer(1, 512)),
            'pass': gen_string('alpha'),
            'quote': False,
            'http_valid': False,
        },
        {
            'login': gen_string('alphanumeric', gen_integer(1, 512)),
            'pass': gen_string('alphanumeric'),
            'quote': False,
            'http_valid': False,
        },
        {
            'login': gen_string('utf8', gen_integer(1, 50)),
            'pass': gen_string('utf8'),
            'quote': True,
            'http_valid': False,
            'encoding': 'utf8',
        },
    ]
    if url_encoded:
        return [
            {
                'login': quote_plus(cred['login'].encode('utf-8'), ''),
                'pass': quote_plus(cred['pass'].encode('utf-8'), ''),
                'http_valid': cred['http_valid'],
                'original_encoding': cred.get('encoding', 'latin-1'),
            }
            for cred in credentials
        ]
    else:
        return credentials


def invalid_http_credentials(url_encoded=False):
    """Returns a list of invalid credentials for HTTP authentication

    :param url_encoded: flag for quoting special characters
    :return: A list of dictionaries with user and password credentials
    """
    credentials = [
        {'login': gen_string('alpha', 1024), 'pass': ''},
        {'login': gen_string('alpha', 512), 'pass': gen_string('alpha', 512)},
        {'login': gen_string('utf8', 256), 'pass': gen_string('utf8', 256)},
    ]
    if url_encoded:
        return [
            {
                'login': quote_plus(cred['login'].encode('utf-8'), ''),
                'pass': quote_plus(cred['pass'].encode('utf-8'), ''),
            }
            for cred in credentials
        ]
    else:
        return credentials


@filtered_datapoint
def invalid_docker_upstream_names():
    """Return a list of various kinds of invalid strings for Docker
    repositories.
    """
    return [
        # boundaries
        add_uppercase_char_into_string(gen_string('alphanumeric', 2)),
        gen_string('alphanumeric', 256).lower(),
        '/'.join(
            [
                add_uppercase_char_into_string(gen_string('alphanumeric', 4)),
                gen_string('alphanumeric', 3),
            ]
        ),
        '/'.join(
            [
                gen_string('alphanumeric', 4),
                add_uppercase_char_into_string(gen_string('alphanumeric', 3)),
            ]
        ),
        '/'.join(
            [gen_string('alphanumeric', 127).lower(), gen_string('alphanumeric', 128).lower()]
        ),
        '/'.join(
            [gen_string('alphanumeric', 128).lower(), gen_string('alphanumeric', 127).lower()]
        ),
        # not allowed non alphanumeric character
        '{0}+{1}_{2}/{2}-{1}_{0}.{3}'.format(
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
        ),
        '{0}-{1}_{2}/{2}+{1}_{0}.{3}'.format(
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
        ),
        '{}-_-_/-_.'.format(gen_string('alphanumeric', 1).lower()),
        '-_-_/{}-_.'.format(gen_string('alphanumeric', 1).lower()),
    ]


@filtered_datapoint
def valid_docker_upstream_names():
    """Return a list of various kinds of valid strings for Docker repositories."""
    return [
        # boundaries
        gen_string('alphanumeric', 1).lower(),
        gen_string('alphanumeric', 255).lower(),
        '/'.join([gen_string('alphanumeric', 1).lower(), gen_string('alphanumeric', 1).lower()]),
        '/'.join(
            [gen_string('alphanumeric', 127).lower(), gen_string('alphanumeric', 127).lower()]
        ),
        # allowed non alphanumeric character
        '{0}-{1}_{2}/{2}-{1}_{0}.{3}'.format(
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
            gen_string('alphanumeric', random.randint(3, 6)).lower(),
        ),
        '{0}-_-_/{0}-_.'.format(gen_string('alphanumeric', 1).lower()),
    ]


@filtered_datapoint
def valid_url_list():
    return [gen_url(scheme="http"), gen_url(scheme="https")]


@filtered_datapoint
def valid_cron_expressions():
    """Returns a list of valid cron expressions"""
    return [
        # After 30 min
        "*/30 * * * *",
        # At noon every day
        "0 12 * * *",
        # Weekdays at 2:00am
        "0 2 * * 1-5",
        # At 15 minutes past the hour, between 01:00 AM and 05:59 AM,
        # on day 2 of the month
        "15 1-5 2 * *",
    ]
