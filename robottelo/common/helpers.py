# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Several helper methods and functions.
"""

import os
import random
import re
import string
import time

from fauxfactory import gen_string, gen_integer
from itertools import izip
from robottelo.common import conf
from urllib2 import urlopen, Request, URLError
from urlparse import urlunsplit


def get_server_credentials():
    """Return credentials for interacting with a Foreman deployment API.

    :return: A username-password pair.
    :rtype: tuple

    """
    return (
        conf.properties['foreman.admin.username'],
        conf.properties['foreman.admin.password']
    )


def get_server_url():
    """Return the base URL of the Foreman deployment being tested.

    The following values from the config file are used to build the URL:

    * ``main.server.scheme`` (default: https)
    * ``main.server.hostname`` (required)
    * ``main.server.port`` (default: none)

    Setting ``port`` to 80 does *not* imply that ``scheme`` is 'https'. If
    ``port`` is 80 and ``scheme`` is unset, ``scheme`` will still default to
    'https'.

    :return: A URL.
    :rtype: str

    """
    # If the config file contains an unset property (e.g. `server.scheme=`),
    # then `conf.properties['main.server.scheme']` will return an empty string.
    # If the config file is missing a property, then fetching that property
    # will throw a KeyError exception. Let's deal with both cases by getting a
    # default value of ''.
    scheme = conf.properties.get('main.server.scheme', '')
    hostname = conf.properties['main.server.hostname']
    port = conf.properties.get('main.server.port', '')

    # As promised in the docstring, we must provide a default scheme.
    if scheme == '':
        scheme = 'https'

    # All anticipated error cases have been handled at this point.
    if port == '':
        return urlunsplit((scheme, hostname, '', '', ''))
    else:
        return urlunsplit((
            scheme, '{0}:{1}'.format(hostname, port), '', '', ''
        ))


def generate_name(minimum=4, maximum=8):
    """
    Generates a random string using lower, upper boundaries to determine the
    length.
    """

    if minimum <= 0:
        minimum = 4
    if maximum < minimum:
        maximum = minimum

    rand = random.SystemRandom()
    pool1 = string.ascii_lowercase + string.digits

    name = u''.join(
        rand.choice(pool1) for x in range(random.randint(minimum, maximum)))

    return unicode(name)


def generate_email_address(name_length=8, domain_length=6):
    """
    Generates a random email address.
    """
    return u'%s@%s.com' % (generate_name(name_length),
                           generate_name(domain_length))


def valid_names_list():
    """
    List of valid names for input testing.
    """
    return [
        generate_name(5, 5),
        generate_name(255),
        u"%s-%s" % (generate_name(4), generate_name(4)),
        u"%s.%s" % (generate_name(4), generate_name(4)),
        u"նոր օգտվող-%s" % generate_name(2),
        u"新用戶-%s" % generate_name(2),
        u"नए उपयोगकर्ता-%s" % generate_name(2),
        u"нового пользователя-%s" % generate_name(2),
        u"uusi käyttäjä-%s" % generate_name(2),
        u"νέος χρήστης-%s" % generate_name(2),
        u"foo@!#$^&*( ) %s" % generate_name(),
        u"<blink>%s</blink>" % generate_name(),
        u"bar+{}|\"?hi %s" % generate_name(),
        u' %s' % generate_name(),
        u'%s ' % generate_name()
    ]


def valid_data_list():
    """
    List of valid data for input testing.
    """
    return [
        gen_string("alpha", 8),
        gen_string("numeric", 8),
        gen_string("alphanumeric", 8),
        gen_string("utf8", 8),
        gen_string("latin1", 8),
        gen_string("html", 8)
    ]


def invalid_names_list():
    """
    List of invalid names for input testing.
    """
    return [
        gen_string("alpha", 300),
        gen_string("numeric", 300),
        gen_string("alphanumeric", 300),
        gen_string("utf8", 300),
        gen_string("latin1", 300),
        gen_string("html", 300),
        gen_string("alpha", 256)
    ]


def generate_ipaddr(ip3=False):
    """
    Generates a random IP address.
    """
    rng = 3 if ip3 else 4
    ipaddr = u'.'.join(str(random.randrange(0, 255, 1)) for x in range(rng))

    return unicode(ipaddr if not ip3 else ipaddr + u'.0')


def generate_mac(delimiter=u':'):
    """
    Generates a random MAC address.
    """
    chars = ['a', 'b', 'c', 'd', 'e', 'f',
             '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    # We'll eventually need to be able to test against all valid
    # (and some invalid!) delimiters, so might as well make it
    # parameterized.  Valid delimiters include (but may not be
    # limited to):  ':', "-", "None"

    mac = delimiter.join(
        chars[random.randrange(0, len(chars), 1)] + chars[random.randrange(
            0, len(chars), 1)] for x in range(6))

    return unicode(mac)


class STR:
    """Stores constants to be used in generate_string function
    """

    alphanumeric = "alphanumeric"
    alpha = "alpha"
    numeric = "numeric"
    html = "html"
    latin1 = "latin1"
    utf8 = "utf8"


def generate_strings_list(len1=8):
    """
    Generates a list of all the input strings
    """
    return [
        gen_string(str_type, gen_integer(3, 30))
        for str_type
        in ('alpha', 'numeric', 'alphanumeric',
            'latin1', 'utf8', 'cjk', 'html')
    ]


def csv_to_dictionary(data):
    """
    Converts CSV data from Hammer CLI and returns a python dictionary.
    """

    records = []

    items = data
    headers = items.pop(0)
    dic_values = [item.split(',') for item in items if len(item) > 0]

    dic_keys = [x.replace(' ', '-').lower() for x in headers.split(',')]

    for value in dic_values:
        records.append(dict(izip(dic_keys, value)))

    return records


def escape_search(term):
    """Wraps a search term in " and escape term's " and \\ characters"""
    strip_term = term.strip()
    return u'"%s"' % strip_term.replace('\\', '\\\\').replace('"', '\\"')


def sleep_for_seconds(guaranteed_sleep=1):
    """
    Sleeps for provided seconds + random(0,1). Defaults to 1 sec.
    @param guaranteed_sleep: Guaranteed sleep in seconds.
    """
    time.sleep(random.uniform(guaranteed_sleep, guaranteed_sleep + 1))


def update_dictionary(default, updates):
    """
    Updates default dictionary with elements from
    optional dictionary.

    @param default: A python dictionary containing the minimal
    required arguments to create a CLI object.
    @param updates: A python dictionary containing attributes
    to overwrite on default dictionary.

    @return default: The modified default python dictionary.
    """

    if updates:
        for key in set(default.keys()).intersection(set(updates.keys())):
            default[key] = updates[key]

    return default


def info_dictionary(result):
    """
    Function for converting result to dictionary, from info function in base..
    """
    # info dictionary
    r = {}
    sub_prop = None  # stores name of the last group of sub-properties
    sub_num = None  # is not None when list of properties

    for line in result.stdout:
        # skip empty lines
        if line == '':
            continue
        if line.startswith(' '):  # sub-properties are indented
            # values are separated by ':' or '=>'
            if line.find(':') != -1:
                key, value = line.lstrip().split(":", 1)
            elif line.find('=>') != -1:
                key, value = line.lstrip().split(" =>", 1)
            else:
                key = value = None

            if key is None and value is None:
                # Parse single attribute collection properties
                # Template
                #  1) template1
                #  2) template2
                #
                # or
                # Template
                #  template1
                #  template2
                match = re.match(r'\d+\)\s+(.+)$', line.lstrip())

                if match is None:
                    match = re.match(r'(.*)$', line.lstrip())

                value = match.group(1)

                if isinstance(r[sub_prop], dict):
                    r[sub_prop] = []

                r[sub_prop].append(value)
            else:
                # some properties have many numbered values
                # Example:
                # Content:
                #  1) Repo Name: repo1
                #     URL:       /custom/4f84fc90-9ffa-...
                #  2) Repo Name: puppet1
                #     URL:       /custom/4f84fc90-9ffa-...
                starts_with_number = re.match(r'(\d+)\)', key)
                if starts_with_number:
                    sub_num = int(starts_with_number.group(1))
                    # no. 1) we need to change dict() to list()
                    if sub_num == 1:
                        r[sub_prop] = []
                    # remove number from key
                    key = re.sub(r'\d+\)', '', key)
                    # append empty dict to array
                    r[sub_prop].append({})

                key = key.lstrip().replace(' ', '-').lower()

                # add value to dictionary
                if sub_num is not None:
                    r[sub_prop][-1][key] = value.lstrip()
                else:
                    r[sub_prop][key] = value.lstrip()
        else:
            sub_num = None  # new property implies no sub property
            key, value = line.lstrip().split(":", 1)
            key = key.lstrip().replace(' ', '-').lower()
            if value.lstrip() == '':  # 'key:' no value, new sub-property
                sub_prop = key
                r[sub_prop] = {}
            else:  # 'key: value' line
                r[key] = value.lstrip()

    # update result
    result.stdout = r

    return result


def download_template(url):
    """
    Function to download the template from given URL
    """
    filename = '/tmp/custom_template'
    if url[0:7] == 'http://' or url[0:8] == 'https://':
        req = Request(url)
        try:
            response = urlopen(req)
        except URLError, err:
            if hasattr(err, 'reason'):
                raise Exception(
                    "Invalid URL, Reason:", err.reason)
            elif hasattr(err, 'code'):
                raise Exception(
                    "The server couldn\'t fulfill the request", err.code)
        else:
            temp_file = open(filename, 'wb')
            temp_file.write(response.read())
            temp_file.close()
            return filename
    else:
        raise Exception(
            "Invalid URL '%s'" % url)


def get_data_file(filename):
    """
    Returns correct path of file from data folder
    """

    path = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                         os.pardir, os.pardir))
    data_file = os.path.join(path, "tests", "foreman", "data", filename)
    if os.path.isfile(data_file):
        return data_file
    else:
        raise Exception(
            "Couldn't locate the data file '%s'" % data_file)


def read_data_file(filename):
    """
    Read the contents of data file
    """
    absolute_file_path = get_data_file(filename)
    with open(absolute_file_path, 'r') as file_contents:
        return file_contents.read()
