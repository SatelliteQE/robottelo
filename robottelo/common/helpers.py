# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Several helper methods and functions.
"""

import os
import random
import string
import time

from itertools import izip
from robottelo.common.constants import HTML_TAGS
from urllib2 import urlopen, Request, URLError


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

    name = str().join(
        rand.choice(pool1) for x in range(random.randint(minimum, maximum)))

    return name


def generate_email_address(name_length=8, domain_length=6):
    """
    Generates a random email address.
    """
    return "%s@%s.com" % (generate_name(name_length),
                          generate_name(domain_length))


def valid_names_list():
    """
    List of valid names for input testing.
    """
    valid_names = [
        generate_name(5, 5).decode('utf-8'),
        generate_name(255).decode('utf-8'),
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
    ]

    return valid_names


def invalid_names_list():
    """
    List of invalid names for input testing.
    """
    invalid_names = [
        " ",
        generate_name(256),
        " " + generate_name(),
        generate_name() + " ",
    ]

    return invalid_names


def generate_ipaddr(ip3=False):
    """
    Generates a random IP address.
    """
    rng = 3 if ip3 else 4
    ipaddr = ".".join(str(random.randrange(0, 255, 1)) for x in range(rng))

    return ipaddr if not ip3 else ipaddr + ".0"


def generate_mac(delimiter=":"):
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
        chars[random.randrange(0, len(chars), 1)]+chars[random.randrange(
            0, len(chars), 1)] for x in range(6))

    return mac


class STR:
    """Stores constants to be used in generate_string function
    """

    alphanumeric = "alphanumeric"
    alpha = "alpha"
    numeric = "numeric"
    html = "html"
    latin1 = "latin1"
    utf8 = "utf8"


def generate_string(str_type, length):
    '''
    This function will allow creation of a wide variety of string types,
    of arbitrary length.  Presently the unicode strings are CJK-only but
    should suffice for the purposes of most multibyte testing.
    '''
    # approximate range of CJK Unified Ideographs
    # It does not include extensions: '4E00- 9FFF'
    # Latin 1 range: '00C0-00F0'
    # (note: includes some mathematical symbol, which sort of wreaks
    # havoc with using full range.  See range broken outto avoid these,
    # below)

    # First lowercase the selected str type
    str_type = str_type.lower()

    if str_type == "alphanumeric":
        output_string = ''.join(
            random.choice(
                string.ascii_letters + string.digits
            ) for i in range(length))
    elif str_type == "alpha":
        output_string = ''.join(
            random.choice(string.ascii_letters) for i in range(length)
        )
    elif str_type == "numeric":
        output_string = ''.join(
            random.choice(string.digits) for i in range(length)
        )
    elif str_type == "latin1":
        range0 = range1 = range2 = []
        range0 = ['00C0', '00D6']
        range1 = ['00D8', '00F6']
        range2 = ['00F8', '00FF']
        output_array = []
        for i in range(int(range0[0], 16), int(range0[1], 16)):
            output_array.append(i)
        for i in range(int(range1[0], 16), int(range1[1], 16)):
            output_array.append(i)
        for i in range(int(range2[0], 16), int(range2[1], 16)):
            output_array.append(i)
        output_string = ''.join(
            unichr(random.choice(output_array)) for x in xrange(length))
        output_string.encode('utf-8')
    elif str_type == "utf8":
        cjk_range = []
        cjk_range = ['4E00', '9FFF']
        output_array = []
        for i in range(int(cjk_range[0], 16), int(cjk_range[1], 16)):
            output_array.append(i)
        output_string = ''.join(
            unichr(random.choice(output_array)) for x in xrange(length))
        output_string.encode('utf-8')
    elif str_type == "html":
        html_tag = random.choice(HTML_TAGS).lower()
        output_string = "<%s>%s</%s>" % (
            html_tag, generate_string("alpha", length), html_tag)
    else:
        raise Exception(
            'Unexpected output type, valid types are \"alpha\", \
            \"alphanumeric\", \"html\", \"latin1\", \"numeric\" or \"utf8\".')
    return output_string


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


def sleep_for_seconds(guaranteed_sleep=1):
    """
    Sleeps for provided seconds + random(0,1). Defaults to 1 sec.
    @param guaranteed_sleep: Guaranteed sleep in seconds.
    """
    time.sleep(random.uniform(guaranteed_sleep, guaranteed_sleep + 1))


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
    data_file = os.path.join(path, "tests", "data", filename)
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
