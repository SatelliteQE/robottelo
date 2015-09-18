# -*- encoding: utf-8 -*-
"""
Usage::

    hammer import [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    activation-key                Import Activation Keys
                                  (from spacewalk-report activation-keys).
    all                           Load ALL data from a specified directory
                                  that is in spacewalk-export format.
    config-file                   Create puppet-modules from Configuration
                                  Channel content (from spacewalk-report
                                  config-files-latest).
    content-host                  Import Content Hosts
                                  (from spacewalk-report system-profiles).
    content-view                  Create Content Views based on local/cloned
                                  Channels (from spacewalk-export-channels).
    host-collection               Import Host Collections
                                  (from spacewalk-report system-groups).
    organization                  Import Organizations
                                  (from spacewalk-report users).
    repository                    Import repositories
                                  (from spacewalk-report repositories).
    repository-enable             Enable any Red Hat repositories
                                  accessible to any Organization
                                  (from spacewalk-report channels).
    template-snippet              Import template snippets
                                  (from spacewalk-report kickstart-scripts).
    user                          Import Users (from spacewalk-report users).

"""
import os
from robottelo import manifests, ssh
from robottelo.cli.base import Base


class Import(Base):
    """Imports configurations from another Satellite instances."""
    command_base = 'import'

    @staticmethod
    def csv_to_dataset(csv_files):
        """Process and return remote CSV files.

        Read the remote CSV files, and return a list of dictionaries for them

        :param csv_files: A list of strings, where each string is a path to
            a CSV file on the remote server.
        :returns: A list of dict, where each dict holds the contents of one CSV
            file.

        """
        result = []
        for csv_file in csv_files:
            ssh_cat = ssh.command(u'cat {0}'.format(csv_file))
            if ssh_cat.return_code != 0:
                raise AssertionError(ssh_cat.stderr)
            csv = ssh_cat.stdout[:-1]
            keys = csv[0].split(',')
            result.extend([
                dict(zip(keys, val.split(',')))
                for val
                in csv[1:]
            ])
        return result

    @staticmethod
    def read_transition_csv(csv_files, key='sat5'):
        """Process remote CSV files and transition them to Dictionary

        The result depends on the order of the processed files. This script
        should mimic the behavior of Katello's hammer-cli-import
        `load_persistent_maps()`_ method.

        :param csv_files: A list of Strings containing absolute paths of the
            remote CSV files
        :param key: (Optional) key to be used to uniquely identify an entity
            ('sat5' by default)
        :returns: A Dictionary object holding the key-value pairs of
            the current state of entity mapping

        .. _load_persistent_maps():
            https://github.com/Katello/hammer-cli-import/blob/master/lib
            /hammer_cli_import/persistentmap.rb#L113

        """
        result = []
        for csv_file in csv_files:
            ssh_cat = ssh.command(u'cat {0}'.format(csv_file))
            if ssh_cat.return_code != 0:
                raise AssertionError(ssh_cat.stderr)
            csv = ssh_cat.stdout[:-1]
            keys = csv[0].split(',')
            for val in csv[1:]:
                record = dict(zip(keys, val.split(',')))
                for entity in result:
                    if entity[key] == record[key]:
                        entity.update(record)
                        break
                else:
                    result.append(record)
        return result

    @classmethod
    def activation_key(cls, options=None):
        """Import Activation Keys (from spacewalk-report activation-keys).
        Requires organization.

        """
        cls.command_sub = 'activation-key'
        return cls.execute(
            cls._construct_command(options),
            output_format='csv'
        )

    @classmethod
    def organization(cls, options=None):
        """Import Organizations (from spacewalk-report users)."""
        cls.command_sub = 'organization'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def user(cls, options=None):
        """Import Users (from spacewalk-report users)."""
        cls.command_sub = 'user'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def host_collection(cls, options=None):
        """Import Host Collections (from spacewalk-report system-groups)."""
        cls.command_sub = 'host-collection'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def config_file(cls, options=None):
        """Create puppet-modules from Configuration Channel content (from
        spacewalk-report config-files-latest).

        """
        cls.command_sub = 'config-file'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def content_host(cls, options=None):
        """Import Content Hosts (from spacewalk-report system-profiles)."""
        cls.command_sub = 'content-host'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def content_view(cls, options=None):
        """Create Content Views based on local/cloned Channels (from
        spacewalk-export-channels).

        """
        cls.command_sub = 'content-view'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def repository(cls, options=None):
        """Import repositories (from spacewalk-report repositories)."""
        cls.command_sub = 'repository'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def repository_enable(cls, options=None):
        """Enable any Red Hat repositories accessible to any Organization
        (from spacewalk-report channels).

        """
        cls.command_sub = 'repository-enable'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def template_snippet(cls, options=None):
        """Import template snippets (from spacewalk-report
        kickstart-scripts).

        """
        cls.command_sub = 'template-snippet'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def all(cls, options=None):
        """Load ALL data from a specified directory that is in spacewalk-export
        format.

        """
        cls.command_sub = 'all'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def activation_key_with_tr_data(cls, options=None):
        """Import Activation Keys (from spacewalk-report activation-keys).
        Requires organization.

        :returns: A tuple of SSHCommandResult and a Dictionary containing the
            transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        result = cls.activation_key(options)
        transition_data = []
        if result.return_code == 0:
            transition_data = cls.read_transition_csv(
                ssh.command(
                    u'ls -v ${HOME}/.transition_data/activation_keys*'
                ).stdout[:-1],
                'org_id'
            )
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)

    @classmethod
    def organization_with_tr_data(cls, options=None):
        """Import Organizations (from spacewalk-report users).

        :returns: A tuple of SSHCommandResult and a Dictionary containing the
            transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        result = cls.organization(options)
        transition_data = []
        if result.return_code == 0:
            transition_data = cls.read_transition_csv(
                ssh.command(
                    u'ls -v ${HOME}/.transition_data/organizations*'
                ).stdout[:-1]
            )
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)

    @classmethod
    def organization_with_tr_data_manifests(cls, options=None):
        """Import Organizations (from spacewalk-report users) with manifests.

        :returns: A tuple of SSHCommandResult and a Dictionary containing
            the transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        # prepare manifests for every organization
        manifest_list = []
        csv_records = cls.csv_to_dataset([options['csv-file']])
        man_dir = ssh.command(u'mktemp -d').stdout[0]
        for org in set([rec['organization'] for rec in csv_records]):
            for char in [' ', '.', '#']:
                org = org.replace(char, '_')
            man_file = manifests.clone()
            ssh.upload_file(man_file, u'{0}/{1}.zip'.format(man_dir, org))
            manifest_list.append(u'{0}/{1}.zip'.format(man_dir, org))
            os.remove(man_file)
        options.update({'upload-manifests-from': man_dir})

        result = cls.organization(options)
        ssh.command(u'rm -rf {}'.format(man_dir))
        transition_data = []
        if result.return_code == 0:
            transition_data = cls.read_transition_csv(
                ssh.command(
                    u'ls -v ${HOME}/.transition_data/organizations*'
                ).stdout[:-1]
            )
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)

    @classmethod
    def user_with_tr_data(cls, options=None):
        """Import Users (from spacewalk-report users).

        :returns: A tuple of SSHCommandResult and a Dictionary containing the
            transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        result = cls.user(options)
        transition_data = []
        if result.return_code == 0:
            transition_data = cls.read_transition_csv(
                ssh.command(
                    u'ls -v ${HOME}/.transition_data/users*'
                ).stdout[:-1]
            )
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)

    @classmethod
    def host_collection_with_tr_data(cls, options=None):
        """Import Host Collections (from spacewalk-report system-groups).

        :returns: A tuple of SSHCommandResult and a Dictionary containing the
            transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        result = cls.host_collection(options)
        transition_data = []
        if result.return_code == 0:
            transition_data = cls.read_transition_csv(
                ssh.command(
                    u'ls -v ${HOME}/.transition_data/host_collections*'
                ).stdout[:-1]
            )
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)

    @classmethod
    def config_file_with_tr_data(cls, options=None):
        """Create puppet-modules from Configuration Channel content (from
        spacewalk-report config-files-latest).

        :returns: A tuple of SSHCommandResult and a List containing the
            transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        result = cls.config_file(options)
        transition_data = []
        if result.return_code == 0:
            transition_data = [
                cls.read_transition_csv(ssh.command(cmd).stdout[:-1], key)
                for cmd, key
                in (
                    (u'ls -v ${HOME}/.transition_data/products*', u'sat5'),
                    (
                        u'ls -v ${HOME}/.transition_data/puppet_repositories*',
                        u'org_id'
                    ),
                )
            ]
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)

    @classmethod
    def content_view_with_tr_data(cls, options=None):
        """Create Content Views based on local/cloned Channels (from
        spacewalk-export-channels).

        :returns: A tuple of SSHCommandResult and a Dictionary containing the
            transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        result = cls.content_view(options)
        transition_data = []
        if result.return_code == 0:
            transition_data = cls.read_transition_csv(
                ssh.command(
                    u'ls -v ${HOME}/.transition_data/content_views*'
                ).stdout[:-1]
            )
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)

    @classmethod
    def repository_with_tr_data(cls, options=None):
        """Import repositories (from spacewalk-report repositories).

        :returns: A tuple of SSHCommandResult and a List containing the
            transition data of the Import
        :raises: AssertionError if a non-zero return code is encountered.

        """
        result = cls.repository(options)
        transition_data = []
        if result.return_code == 0:
            transition_data = [
                cls.read_transition_csv(
                    ssh.command(cmd).stdout[:-1], key
                )
                for cmd, key
                in (
                    (u'ls -v ${HOME}/.transition_data/products*', u'org_id'),
                    (u'ls -v ${HOME}/.transition_data/repositories*', u'sat5'),
                )
            ]
        else:
            raise AssertionError(result.stderr)
        return (result, transition_data)
