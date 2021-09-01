"""Generate hammer command tree in json format by inspecting every command's
help.

"""
import json

from robottelo import ssh
from robottelo.cli import hammer


def generate_command_tree(command):
    """Recursively walk trhough the hammer commands and subcommands and fetch
    their help. Return a dictionary with the contents.

    """
    output = ssh.command(f'{command} --help').stdout
    contents = hammer.parse_help(output)
    if len(contents['subcommands']) > 0:
        for subcommand in contents['subcommands']:
            subcommand.update(generate_command_tree('{} {}'.format(command, subcommand['name'])))
    return contents


# Generate the json file in the working directory
with open('hammer_commands.json', 'w') as f:
    f.write(json.dumps(generate_command_tree('hammer'), indent=2, sort_keys=True))
