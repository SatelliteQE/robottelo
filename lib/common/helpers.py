#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import random
import string

def generate_name(min=4, max=8):

    if min <= 0:
        min = 4
    if max < min:
        max = min

    r = random.SystemRandom()
    pool1 = string.ascii_lowercase + string.digits

    return "%s" % str().join(r.choice(pool1) for x in range(random.randint(min, max)))

def valid_names_list():

    VALID_NAMES = [
        generate_name(5,5),
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

def i18n_join (range_begin, range_end, length):
    '''
    This function is primarily for use with the generate_string()
    function, for use with manipulating i18n strings.
    '''
    output_array = []
    for i in range(int(range_begin, 16), int(range_end, 16)):
        output_array.append(i)
    i18n_output = ''.join(unichr(random.choice(output_array)) for x in xrange(length))
    return i18n_output

def generate_string (str_type, length):
    '''
    This function will allow creation of a wide variety of string types,
    of arbitrary length.  Presently the unicode strings are CJK-only but
    should suffice for the purposes of most multibyte testing.
    '''
    # approximate range of CJK Unified Ideographs
    # It does not include extensions.
    utf8_begin = '4E00'
    utf8_end = '9FFF'
    # range of latin-1 characters/letters (ISO 8859-1)
    # It does not include unicode Latin Extensions.
    latin1_begin = '00C0'
    latin1_end = '00F0'
    if  str_type == "alphanumeric":
        output_string = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(length))
    elif str_type == "alpha":
        output_string = ''.join(random.choice(string.ascii_letters) for i in range(length))
    elif str_type == "numeric":
        output_string = ''.join(random.choice(string.digits) for i in range(length))
    elif str_type == "latin1":
        output_string = i18n_join(latin1_begin, latin1_end, length) 
    elif str_type == "utf8":
        output_string = i18n_join(utf8_begin, utf8_end, length)
    else:
        raise Exception('Unexpected output type, valid types are "alphanumeric", "alpha", "numeric", "latin1", "utf8"')
    return output_string
