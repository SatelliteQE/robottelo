# -*- encoding: utf-8 -*-
"""Data Factory for all entities"""
import random

from functools import wraps
from fauxfactory import gen_string, gen_integer, _make_unicode
from robottelo.config import settings
from robottelo.constants import STRING_TYPES, HTML_TAGS
from robottelo.decorators import bz_bug_is_open
from robottelo.upgrade import get_all_yaml_data, get_yaml_field_value
from six.moves.urllib.parse import quote_plus


class InvalidArgumentError(Exception):
    """Indicates an error when an invalid argument is received."""


def filtered_datapoint(func):
    """Overrides the data creator functions in this class to return 1 value

    If run_one_datapoint=false, return the entire data set. (default: False)
    If run_one_datapoint=true, return a random data.

    """

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        """Perform smoke test attribute check"""
        dataset = func(*args, **kwargs)
        if settings.run_one_datapoint:
            dataset = [random.choice(dataset)]
        return dataset

    return func_wrapper


@filtered_datapoint
def generate_strings_list(length=None, exclude_types=None, bug_id=None,
                          min_length=3, max_length=30):
    """Generates a list of different input strings.

    :param int length: Specifies the length of the strings to be
        be generated. If the len1 is None then the list is
        returned with string types of random length.
    :param exclude_types: Specify a list of data types to be removed from
        generated list. example: exclude_types=['html', 'cjk']
    :param int bug_id: Specify any bug id that is associated to the datapoint
        specified in remove_str.  This will be used only when remove_str is
        populated.
    :param int min_length: Minimum length to be used in integer generator
    :param int max_length: Maximum length to be used in integer generator
    :returns: A list of various string types.

    """
    if length is None:
        length = gen_integer(min_length, max_length)

    strings = {
        str_type: gen_string(str_type, length)
        for str_type in STRING_TYPES
    }

    # Handle No bug_id, If some entity doesn't support a str_type.
    # Remove str_type from dictionary only if bug is open.
    if exclude_types and (bug_id is None or bz_bug_is_open(bug_id)):
        for item in exclude_types:
            strings.pop(item, None)

    return list(strings.values())


@filtered_datapoint
def invalid_emails_list():
    """Returns a list of invalid emails."""
    return [
        u'foreman@',
        u'@foreman',
        u'@',
        u'Abc.example.com',
        u'A@b@c@example.com',
        u'email@example..c',
        # total length 255:
        u'{0}@example.com'.format(gen_string('alpha', 243)),
        u'{0}@example.com'.format(gen_string('html')),
        u's p a c e s@example.com',
        u'dot..dot@example.com'
    ]


@filtered_datapoint
def invalid_id_list():
    """Generates a list of invalid IDs."""
    return [
        gen_string('alpha'),
        None,
        u'',
        -1,
    ]


@filtered_datapoint
def invalid_names_list():
    """Generates a list of invalid names."""
    return generate_strings_list(300)


@filtered_datapoint
def invalid_usernames_list():
    return [
        '',
        'space {0}'.format(gen_string('alpha')),
        gen_string('alpha', 101),
        gen_string('html')
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
        raise InvalidArgumentError(
            'Valid interface values are {0}'.format('api, cli, ui only')
        )
    if interface == 'ui':
        return ['', ' '] + invalid_names_list()
    else:  # interface = api or cli or None
        return ['', ' ', '\t'] + invalid_names_list()


@filtered_datapoint
def valid_data_list():
    """Generates a list of valid input values.

    Note:
    Although this helper is widely used for different attributes for several
    entities, the following are known behaviors and are handled specifically in
    the corresponding test modules::

        Org - name max length is 242
        Loc - name max length is 246

    """
    return [
        gen_string('alphanumeric', random.randint(1, 255)),
        gen_string('alpha', random.randint(1, 255)),
        gen_string('cjk', random.randint(1, 85)),
        gen_string('latin1', random.randint(1, 255)),
        gen_string('numeric', random.randint(1, 255)),
        gen_string('utf8', random.randint(1, 85)),
        gen_string('html', random.randint(1, 85)),
    ]


@filtered_datapoint
def valid_emails_list():
    """Returns a list of valid emails."""
    return [
        u'{0}@example.com'.format(gen_string('alpha')),
        u'{0}@example.com'.format(gen_string('alphanumeric')),
        u'{0}@example.com'.format(gen_string('numeric')),
        u'{0}@example.com'.format(gen_string('alphanumeric', 48)),
        u'{0}+{1}@example.com'.format(
            gen_string('alphanumeric'),
            gen_string('alphanumeric'),
        ),
        u'{0}.{1}@example.com'.format(
            gen_string('alphanumeric'),
            gen_string('alphanumeric'),
        ),
        u'"():;"@example.com',
        u'!#$%&*+-/=?^`{|}~@example.com',
    ]


@filtered_datapoint
def valid_environments_list():
    """Returns a list of valid environment names"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
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
        gen_string(
            'alphanumeric', random.randint(1, (255 - 6 - domain_length))
        ).lower(),
        gen_string(
            'alpha', random.randint(1, (255 - 6 - domain_length))).lower(),
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
        u"{0}-{1}".format(gen_string('utf8', 4), gen_string('utf8', 4)),
        u"{0}.{1}".format(gen_string('utf8', 4), gen_string('utf8', 4)),
        u"նոր օգտվող-{0}".format(gen_string('utf8', 2)),
        u"新用戶-{0}".format(gen_string('utf8', 2)),
        u"नए उपयोगकर्ता-{0}".format(gen_string('utf8', 2)),
        u"нового пользователя-{0}".format(gen_string('utf8', 2)),
        u"uusi käyttäjä-{0}".format(gen_string('utf8', 2)),
        u"νέος χρήστης-{0}".format(gen_string('utf8', 2)),
        u"foo@!#$^&*( ) {0}".format(gen_string('utf8')),
        u"<blink>{0}</blink>".format(gen_string('utf8')),
        u"bar+{{}}|\"?hi {0}".format(gen_string('utf8')),
        u' {0}'.format(gen_string('utf8')),
        u'{0} '.format(gen_string('utf8')),
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
    return generate_strings_list(
        exclude_types=['html'],
        min_length=1,
        max_length=50
    )


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
        {
            u'login': 'admin',
            u'pass': 'changeme',
            u'quote': False,
            u'http_valid': True,
        },
        {
            u'login': '@dmin',
            u'pass': 'changeme',
            u'quote': True,
            u'http_valid': True,
        },
        {
            u'login': 'adm/n',
            u'pass': 'changeme',
            u'quote': False,
            u'http_valid': True,
        },
        {
            u'login': 'admin2',
            u'pass': 'ch@ngeme',
            u'quote': True,
            u'http_valid': True,
        },
        {
            u'login': 'admin3',
            u'pass': 'chan:eme',
            u'quote': False,
            u'http_valid': True,
        },
        {
            u'login': 'admin4',
            u'pass': 'chan/eme',
            u'quote': True,
            u'http_valid': True,
        },
        {
            u'login': 'admin5',
            u'pass': 'ch@n:eme',
            u'quote': True,
            u'http_valid': True,
        },
        {
            u'login': '0',
            u'pass': 'mypassword',
            u'quote': False,
            u'http_valid': True,
        },
        {
            u'login': '0123456789012345678901234567890123456789',
            u'pass': 'changeme',
            u'quote': False,
            u'http_valid': True,
        },
        {
            u'login': 'admin',
            u'pass': '',
            u'quote': False,
            u'http_valid': False,
        },
        {
            u'login': '',
            u'pass': 'mypassword',
            u'quote': False,
            u'http_valid': False,
        },
        {
            u'login': '',
            u'pass': '',
            u'quote': False,
            u'http_valid': False,
        },
        {
            u'login': gen_string('alpha', gen_integer(1, 512)),
            u'pass': gen_string('alpha'),
            u'quote': False,
            u'http_valid': False,
        },
        {
            u'login': gen_string('alphanumeric', gen_integer(1, 512)),
            u'pass': gen_string('alphanumeric'),
            u'quote': False,
            u'http_valid': False,
        },
        {
            u'login': gen_string('utf8', gen_integer(1, 50)),
            u'pass': gen_string('utf8'),
            u'quote': True,
            u'http_valid': False,
        },
    ]
    if url_encoded:
        return [{
            u'login': quote_plus(cred['login'].encode('utf-8'), ''),
            u'pass': quote_plus(cred['pass'].encode('utf-8'), ''),
            u'http_valid': cred['http_valid'],
        } for cred in credentials]
    else:
        return credentials


def invalid_http_credentials(url_encoded=False):
    """Returns a list of invalid credentials for HTTP authentication

    :param url_encoded: flag for quoting special characters
    :return: A list of dictionaries with user and password credentials
    """
    credentials = [
        {u'login': gen_string('alpha', 1024), u'pass': ''},
        {
            u'login': gen_string('alpha', 512),
            u'pass': gen_string('alpha', 512)
        },
        {u'login': gen_string('utf8', 256), u'pass': gen_string('utf8', 256)},
    ]
    if url_encoded:
        return [{
            u'login': quote_plus(cred['login'].encode('utf-8'), ''),
            u'pass': quote_plus(cred['pass'].encode('utf-8'), '')
        }
            for cred in credentials]
    else:
        return credentials


@filtered_datapoint
def get_valid_preupgrade_data(test_entity, field):
    """Returns valid list of tuples for given test_entity and field from
    preUpgrade YAML file

    :param str test_entity: The test_entity name in YAML file
        e.g. Organization-Tests to check it exists and its associations
    :param str field: Field name in YAML for which the test created
        e.g. name to check if the test_entity exists by name
        e.g. smart-proxy to check association with test_entity
    :return: List of tuples. Tuple containing pair of SubEntity, field_value
        e.g. [('Default Organization',2),('another_org',5)], where 2 and 5 are
        ids(field) of two mentioned orgs(subEntity)
    """
    datalist = []
    test_entity = test_entity.lower()
    field = field.lower()
    for entity in get_all_yaml_data()[test_entity].keys():
        field_data = get_yaml_field_value(test_entity, entity, field)
        if field_data is None:
            continue
        elif type(field_data) == list:
            for value in field_data:
                datalist.append((entity, value))
        else:
            datalist.append((entity, field_data))
    if not datalist:
        raise InvalidArgumentError('No such field/test \'{0}\' exists in YAML'
                                   'file under {1}'.format(field, test_entity))
    return datalist


def gen_html_with_total_len(length=10):
    """Returns a random string made up of html characters.
    This differ from fauxfactory gen_html because length takes html tag into
    account
    :param int length: Length for random data.
    :returns: A random string made up of html characters.
    :rtype: str

    """
    if length < 8:
        raise ValueError('Impossible generate html with len less then 7')

    random.seed()
    html_tag = random.choice(HTML_TAGS)
    maybe_len = length - (len(html_tag) * 2 + 5)
    if maybe_len <= 0:
        length -= 7
        html_tag = 'a'
    else:
        length = maybe_len
    output_string = u'<{0}>{1}</{2}>'.format(
        html_tag, gen_string("alpha", length), html_tag)

    return _make_unicode(output_string)
