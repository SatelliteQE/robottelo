# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Several helper methods and functions.
"""

import os
import re

from automation_tools import distro_info
from fabric.api import execute, settings
from fauxfactory import gen_string, gen_integer
from itertools import izip
from robottelo.common import conf
from robottelo.common.decorators import bz_bug_is_open
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


def get_internal_docker_url():
    """Returns the docker internal server url config

    If the variable ``{server_hostname}`` is found in the string, it will be
    replaced by ``main.server.hostname`` from the config file.

    """
    internal_url = conf.properties.get('docker.internal_url')
    if internal_url is not None:
        internal_url = internal_url.format(
            server_hostname=conf.properties['main.server.hostname'])
    return internal_url


def get_external_docker_url():
    """Returns the docker external server url config"""
    return conf.properties.get('docker.external_url')


def get_distro_info():
    """Get a tuple of information about the RHEL distribution on the server.

    :return: A tuple of information in this format: ``('rhel', 6, 6)``.
    :rtype: tuple

    """
    with settings(
        key_filename=conf.properties['main.server.ssh.key_private'],
        user=conf.properties['main.server.ssh.username'],
    ):
        hostname = conf.properties['main.server.hostname']
        return execute(distro_info, host=hostname)[hostname]


def valid_names_list():
    """
    List of valid names for input testing.
    """
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


class STR:
    """Stores constants to be used in generate_string function
    """

    alphanumeric = "alphanumeric"
    alpha = "alpha"
    numeric = "numeric"
    html = "html"
    latin1 = "latin1"
    utf8 = "utf8"


def generate_strings_list(len1=None, remove_str=None, bug_id=None):
    """Generates a list of all the input strings.

    :param int len1: Specifies the length of the strings to be
        be generated. If the len1 is None then the list is
        returned with string types of random length.
    :return: Returns a list of various string types.
    :rtype: list

    """
    if len1 is None:
        len1 = gen_integer(3, 30)
    strings = {
        str_type: gen_string(str_type, len1)
        for str_type
        in (u'alpha', u'numeric', u'alphanumeric',
            u'latin1', u'utf8', u'cjk', u'html')
    }
    # Handle No bug_id, If some entity doesn't support a str_type.
    # Remove str_type from dictionary only if bug is open.
    if remove_str and (bug_id is None or bz_bug_is_open(bug_id)):
        del strings[remove_str]
    return list(strings.values())


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
