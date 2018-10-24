"""Helpers to interact with hammer command line utility."""
import csv
import json

import re
import six
from six import text_type
from six.moves import cStringIO as StringIO
from six.moves import zip


def _csv_reader(output):
    """An unicode CSV reader which processes unicode strings and return unicode
    strings data.

    This is needed because the builtin module does not support unicode strings,
    from Python 2 docs::

        Note: This version of the csv module doesn't support Unicode input.
        Also, there are currently some issues regarding ASCII NUL characters.
        Accordingly, all input should be UTF-8 or printable ASCII to be safe;"

    On Python 3 this generator is not needed because the default string type is
    unicode.

    :param output: can be any object which supports the iterator protocol and
    returns a unicode string each time its next() method is called.
    :return: generator that will yield a list of unicode string values.

    """
    data = '\n'.join(output)
    if six.PY2:
        data = data.encode('utf8')
    handler = StringIO(data)

    for row in csv.reader(handler):  # pragma: no cover
        if six.PY2:
            yield [value.decode('utf8') for value in row]
        else:
            yield row


def _normalize(header):
    """Replace empty spaces with '-' and lower all chars
    """
    return header.replace(' ', '-').lower()


def parse_json(stdout):
    """Parse JSON output from Hammer CLI and convert it to python dictionary
    while normalizing keys.
    """
    parsed = json.loads(stdout)
    return _normalize_obj(parsed)


def _normalize_obj(obj):
    """Normalize all dict's keys replacing empty spaces with "-" and lowering
    chars
    """
    if isinstance(obj, dict):
        return {_normalize(k): _normalize_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_normalize_obj(v) for v in obj]
    # doing this to conform to csv parser
    elif isinstance(obj, int) and not isinstance(obj, bool):
        return text_type(obj)
    return obj


def parse_csv(output):
    """Parse CSV output from Hammer CLI and convert it to python dictionary."""
    reader = _csv_reader(output)
    # Generate the key names, spaces will be converted to dashes "-"
    keys = [_normalize(header) for header in next(reader)]
    # For each entry, create a dict mapping each key with each value
    return [dict(zip(keys, values)) for values in reader if len(values) > 0]


def parse_help(output):
    """Parse the help output from a hammer command and return a dictionary
    mapping the subcommands and options accepted by that command.

    """
    # Parsing states
    state = 0
    subcommands_section_state = 1
    options_section_state = 2

    contents = {
        'subcommands': [],
        'options': [],
    }
    option_regex = re.compile(
        r'^ (-(?P<shortname>\w), )?(--(?P<name>[\w-]+))?'
        r'(, --(?P<deprecation_name>[\w-]+))?( (?P<value>\w+))?\s+(?P<help>.*)$'
    )
    subcommand_regex = re.compile(
        r'^ (?P<name>[\w-]+)?\s+(?P<description>.*)$'
    )

    for line in output:
        if len(line.strip()) == 0:
            continue
        if line.startswith('Subcommands:'):
            state = subcommands_section_state
            continue
        if line.startswith('Options:'):
            state = options_section_state
            continue

        if state == subcommands_section_state:
            match = subcommand_regex.search(line)
            if match is None:  # pragma: no cover
                continue
            if match.group('name') is None:
                contents['subcommands'][-1]['description'] += (
                    u' {0}'.format(match.group('description'))
                )
            else:
                contents['subcommands'].append({
                    u'name': match.group('name'),
                    u'description': match.group('description'),
                })
        if state == options_section_state:
            match = option_regex.search(line)
            if match is None:  # pragma: no cover
                continue
            if match.group('name') is None:
                contents['options'][-1]['help'] += (
                    u' {0}'.format(match.group('help'))
                )
            else:
                contents['options'].append({
                    u'name': match.group('name'),
                    u'shortname': match.group('shortname'),
                    u'value': match.group('value'),
                    u'help': match.group('help'),
                })

    return contents


def get_line_indentation_spaces(line, tab_spaces=4):
    """Return the number of spaces chars the line begin with

    :param str line: the line string to parse
    :param int tab_spaces: The tab char is represent how many spaces
    """
    if not line or len(line) < tab_spaces:
        return 0
    spaces = 0
    for char in line:
        if char not in (' ', '\t'):
            break
        if char == '\t':
            spaces += tab_spaces
        else:
            spaces += 1

    return spaces


def get_line_indentation_level(line, tab_spaces=4, indentation_spaces=4):
    """Return the indentation level

    :param str line: the line string to parse
    :param int tab_spaces: The tab char is represent how many spaces
    :param indentation_spaces: how much spaces represent an indentation level

    Note::

        suppose we have the following lines:
        '''
        level 0
            level 1
                level 2
        '''
        assert get_line_indentation_level('level 0') == 0
        assert get_line_indentation_level('    level 1') == 1
        assert get_line_indentation_level('        level 2') == 2

    """
    return get_line_indentation_spaces(
        line, tab_spaces=tab_spaces)//indentation_spaces


def parse_info(output):
    """Parse the info output and returns a dict mapping the values."""
    # info dictionary
    contents = {}
    sub_prop = None  # stores name of the last group of sub-properties
    sub_num = None  # is not None when list of properties
    second_level_key = None  # is set when a possible second level is detected

    for line in output:
        # skip empty lines
        if line == '':
            continue
        current_indent_level = get_line_indentation_level(line)
        if current_indent_level <= 1:
            # we are entering or leaving a second level from lower/upper levels
            # clear the second level key
            second_level_key = None
        if line.startswith(' '):  # sub-properties are indented
            # values are separated by ':' or '=>', but not by '::' which can be
            # entity name like 'test::params::keys'
            if line.find(':') != -1 and not line.find('::') != -1:
                key, value = line.lstrip().split(":", 1)
            elif line.find('=>') != -1 and len(
                    line.lstrip().split(" =>", 1)) == 2:
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

                if isinstance(contents[sub_prop], dict):
                    contents[sub_prop] = []

                contents[sub_prop].append(value)
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
                        contents[sub_prop] = []
                    # remove number from key
                    key = re.sub(r'\d+\)', '', key)
                    # append empty dict to array
                    contents[sub_prop].append({})

                key = key.lstrip().replace(' ', '-').lower()
                value = value.lstrip()
                # add value to dictionary
                if sub_num is not None:
                    contents[sub_prop][-1][key] = value
                else:
                    # a third level is always represented as a dictionary and
                    # we need to detect if we are at third level
                    # example:
                    # Content Information:
                    #     Content View:
                    #         ID:   10
                    #         Name: Default Organization View
                    # the "ID" and "Name" are located at third indent level
                    # "content view" is located at second indent level
                    if current_indent_level == 2 and second_level_key:
                        # we are at third level indentation
                        if not contents[sub_prop][second_level_key]:
                            contents[sub_prop][second_level_key] = {}
                        contents[sub_prop][second_level_key][key] = value
                    else:
                        contents[sub_prop][key] = value
                    if current_indent_level == 1 and not value:
                        # always set the last possible second level key
                        # that can form a third level
                        second_level_key = key
        else:
            sub_num = None  # new property implies no sub property
            key, value = line.lstrip().split(":", 1)
            key = key.lstrip().replace(' ', '-').lower()
            if value.lstrip() == '':  # 'key:' no value, new sub-property
                sub_prop = key
                contents[sub_prop] = {}
            else:  # 'key: value' line
                contents[key] = value.lstrip()

    return contents
