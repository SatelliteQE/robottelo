#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import random
import string

from itertools import izip


def generate_name(min=4, max=8):

    if min <= 0:
        min = 4
    if max < min:
        max = min

    r = random.SystemRandom()
    pool1 = string.ascii_lowercase + string.digits

    name = str().join(r.choice(pool1) for x in range(random.randint(min, max)))

    return name


def valid_names_list():

    VALID_NAMES = [
        generate_name(5, 5),
        generate_name(255),
        "%s-%s" % (generate_name(4), generate_name(4)),
        "%s.%s" % (generate_name(4), generate_name(4)),
        u"նոր օգտվող-%s" % generate_name(2),
        u"新用戶-%s" % generate_name(2),
        u"नए उपयोगकर्ता-%s" % generate_name(2),
        u"нового пользователя-%s" % generate_name(2),
        u"uusi käyttäjä-%s" % generate_name(2),
        u"νέος χρήστης-%s" % generate_name(2),
        "foo@!#$^&*( ) %s" % generate_name(),
        "<blink>%s</blink>" % generate_name(),
        "bar+{}|\"?hi %s" % generate_name(),
    ]

    return VALID_NAMES


def invalid_names_list():

    INVALID_NAMES = [
        " ",
        generate_name(256),
        " " + generate_name(),
        generate_name() + " ",
    ]

    return INVALID_NAMES


def generate_ipaddr():

    ipaddr = ".".join(str(random.randrange(0, 255, 1)) for x in range(4))

    return ipaddr


def generate_mac():
    chars = ['a', 'b', 'c', 'd', 'e', 'f',
             '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    mac = ":".join(
        chars[random.randrange(0, len(chars), 1)]+chars[random.randrange(
            0, len(chars), 1)] for x in range(6))

    return mac


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
    else:
        raise Exception(
            'Unexpected output type, valid types are "alphanumeric", \
            "alpha", "numeric", "latin1", "utf8"')
    return output_string


def csv_to_dictionary(data):
    """
    Converts CSV data from Hammer CLI and returns a python dictionary.
    """

    records = []

    items = "".join(data).split('\n')
    headers = items.pop(0)
    entries = [item.split(',') for item in items if len(item) > 0]

    for entry in entries:
        records.append(dict(izip(headers.split(','), entry)))

    return records


def generate_ip3():
    """
    generates random IP in a form of [1-255].[0-255].[0-255].0
    """
    ip1 = str(int(generate_string('numeric', 7)) % 255 + 1)  # to be >0
    ip2 = str(int(generate_string('numeric', 7)) % 256)
    ip3 = str(int(generate_string('numeric', 7)) % 256)
    return "%s.%s.%s.0" % (ip1, ip2, ip3)
