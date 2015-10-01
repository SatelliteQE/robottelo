"""Test utilities for writing Pulp tests

Part of functionalities of Pulp are defined in this module
and have utilities of single repository synchronization, single
sequential repository sync, sequential repository re-sync.

"""
import logging

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.repository import Repository

LOGGER = logging.getLogger(__name__)


class Pulp(object):
    """Performance Measurement of RH Satellite 6

    Pulp Synchronization functionality

    """
    @classmethod
    def repository_single_sync(cls, repo_id, repo_name, thread_id):
        """Single Synchronization

        :param str repo_id: Repository id to be synchronized
        :param str repo_name: Repository name
        :return: time measure for a single sync
        :rtype: float

        """
        LOGGER.info(
            'Synchronize {0} by thread-{1}:'
            .format(repo_name, thread_id)
        )

        result = Repository.synchronize(
            {'id': repo_id},
            return_raw_response=True
        )

        if result.return_code != 0:
            LOGGER.error(
                'Sync repository {0} by thread-{1} failed!'
                .format(repo_name, thread_id)
            )
            return 0
        LOGGER.info(
            'Sync repository {0} by thread-{1} successful!'
            .format(repo_name, thread_id)
        )
        return cls.get_elapsed_time(result.stderr)

    @staticmethod
    def get_elapsed_time(stderr):
        """retrieve time from stderr"""
        # should return only one time point as a single sync
        real_time = ''
        for line in stderr.split('\n'):
            if line.startswith('real'):
                real_time = line
        return 0 if real_time == '' else float(real_time.split(' ')[1])

    @staticmethod
    def get_enabled_repos(org_id):
        """Get all enabled repositories ids and names

        :return map_repo_name_id: The dictionary contains all enabled
            repositories in Satellite. Map repo-name as key, repo-id as value
        :raises ``RumtimeException`` if there's no enabled repository in
            default organization denoted by ``org_id``

        """
        LOGGER.info('Searching for enabled repositories by hammer CLI:')

        try:
            result = Repository.list(
                {'organization-id': org_id},
                per_page=False
            )
        except CLIReturnCodeError:
            raise RuntimeError(
                'No enabled repository found in organization {0}!'
                .format(org_id)
            )
        # map repository name with id
        map_repo_name_id = {}
        for repo in result:
            map_repo_name_id[repo['name']] = repo['id']
        return map_repo_name_id

    @classmethod
    def repositories_sequential_sync(
            cls,
            repo_names_list,
            map_repo_name_id,
            sync_iterations,
            savepoint=None):
        """Sync all repositories linearly, and repeat X times

        :param list repo_names_list: A list of targeting repository names
        :param int sync_iterations: The number of times to repeat sync
        :return time_result_dict_sync
        :rtype: dict

        """
        # Create a dictionary to store all timing results from each sync
        time_result_dict_sync = {}

        # repeat sequential sync X times
        for i in range(sync_iterations):
            # note: name key by thread to adapt to graph module
            key = 'thread-{0}'.format(i)
            time_result_dict_sync[key] = []

            # Sync each repo one-by-one and collect timing data
            for repo_name in repo_names_list:
                repo_id = map_repo_name_id.get(repo_name, None)
                if repo_id is None:
                    LOGGER.warning(
                        'Invalid repository name {}!'.format(repo_name)
                    )
                    continue
                LOGGER.debug(
                    'Sequential Sync {0} attempt {1}:'.format(repo_name, i)
                )
                # sync repository once at a time
                time_result_dict_sync[key].append(
                    cls.repository_single_sync(repo_id, repo_name, 'linear')
                )
            # for resync purpose, no need to restore
            if savepoint is None:
                return
            else:
                # restore database at the end of each iteration
                cls._restore_from_savepoint(savepoint)

        return time_result_dict_sync

    @staticmethod
    def _restore_from_savepoint(savepoint):
        """Restore from savepoint"""
        if savepoint == '':
            LOGGER.warning('No savepoint while continuing test!')
            return
        LOGGER.info('Reset db from /home/backup/{0}'.format(savepoint))
        ssh.command('./reset-db.sh /home/backup/{0}'.format(savepoint))
