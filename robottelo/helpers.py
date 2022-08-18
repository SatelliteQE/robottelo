"""Several helper methods and functions."""
from urllib.parse import urljoin  # noqa

from nailgun.config import ServerConfig

from robottelo.config import get_credentials
from robottelo.config import get_url


def get_nailgun_config(user=None):
    """Return a NailGun configuration file constructed from default values.

    :param user: The ```nailgun.entities.User``` object of an user with additional passwd
        property/attribute

    :return: ``nailgun.config.ServerConfig`` object, populated from user parameter object else
        with values from ``robottelo.config.settings``

    """
    creds = (user.login, user.passwd) if user else get_credentials()
    return ServerConfig(get_url(), creds, verify=False)


# --- Issue based Pytest markers ---


def idgen(val):
    """
    The id generator function which will return string that will append to the parameterized
    test name
    """
    return '_parameter'


class InstallerCommand:
    """This class constructs, parses, updates and gets formatted installer commands"""

    def __init__(self, *args, command='satellite-installer', allow_dupes=False, **kwargs):
        """This allows multiple methods for InstallerClass creation

        InstallerCommand('f', 'verbose', command='satellite-installer', sat_host='my_sat')
        InstallerCommand(installer_args=['f', 'verbose'], sat_host='my_sat')
        InstallerCommand(installer_args=['f', 'verbose'], installer_opts={'sat_host': 'my_sat'})

        :param allow_dupes: Allow duplicate options, doesn't apply to future updates

        """

        self.command = command
        self.args = kwargs.pop('installer_args', [])
        self.opts = kwargs.pop('installer_opts', {})
        self.update(*args, allow_dupes=allow_dupes, **kwargs)

    def get_command(self):
        """Construct the final command in the form of a string"""
        command_str = self.command
        for arg in self.args:
            command_str += f' {"-" if len(arg) == 1 else "--"}{arg}'
        for key, val in self.opts.items():
            # if we have duplicate keys (list of values), add each option/value pair
            if isinstance(val, list):
                for v in val:
                    command_str += f' --{key.replace("_", "-")} {v}'
            else:
                command_str += f' --{key.replace("_", "-")} {val}'
        return command_str

    def update(self, *args, allow_dupes=False, **kwargs):
        """Update one or more arguments and options
        values passed as positional and keyword arguments
        """
        new_args = [arg for arg in args if arg not in self.args]
        self.args.extend(new_args)
        if not allow_dupes:
            self.opts.update(kwargs)
        # iterate over all keyword arguments passed in
        for key, val in kwargs.items():
            # if we won't want duplicate keys, override the current value
            if not allow_dupes:
                self.opts[key] = val
            # if we do want duplicate keys, convert the value to a list
            elif curr_val := self.opts.get(key):  # noqa: E203
                val = [val]
                if not isinstance(curr_val, list):
                    curr_val = [curr_val]
                # and add the old value(s) to the new list
                val += curr_val
            self.opts[key] = val

    @classmethod
    def from_cmd_str(cls, command='satellite-installer', cmd_str=None):
        """Construct the class based on a string representing expected installer options.
        This is mostly used for capsule-certs-generate output parsing.
        """
        installer_command, listening = '', False
        for line in cmd_str.splitlines():
            if line.strip().startswith(command):
                listening = True
            if listening:
                installer_command += ' ' + ' '.join(line.replace('\\', '').split())
        installer_command = installer_command.replace(command, '').strip()
        cmd_args, add_later = {}, []
        for opt in installer_command.split('--'):
            if opt := opt.strip().split():  # noqa: E203
                if opt[0] in cmd_args:
                    add_later.append(opt)
                else:
                    cmd_args[opt[0]] = opt[1]
        installer = cls(command=command, installer_opts=cmd_args)
        for opt in add_later:
            installer.update(allow_dupes=True, **{opt[0]: opt[1]})
        return installer

    def __repr__(self):
        """Custom repr will give the constructed command output"""
        return self.get_command()
