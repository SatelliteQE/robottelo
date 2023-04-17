import time
from datetime import datetime

from robottelo.constants import PUPPET_CAPSULE_INSTALLER
from robottelo.constants import PUPPET_COMMON_INSTALLER_OPTS
from robottelo.logging import logger
from robottelo.utils.installer import InstallerCommand


class EnablePluginsCapsule:
    """Miscellaneous settings helper methods"""

    def enable_puppet_capsule(self, satellite=None):
        # Set Satellite URL for puppet-server-foreman-url
        if satellite is not None:
            satellite_url = f'https://{satellite.hostname}'
            PUPPET_COMMON_INSTALLER_OPTS['puppet-server-foreman-url'] = satellite_url
        enable_capsule_cmd = InstallerCommand(
            installer_args=PUPPET_CAPSULE_INSTALLER, installer_opts=PUPPET_COMMON_INSTALLER_OPTS
        )
        result = self.execute(enable_capsule_cmd.get_command(), timeout='20m')
        assert result.status == 0
        assert 'Success!' in result.stdout
        return self


class CapsuleInfo:
    """Miscellaneous Capsule helper methods"""

    def wait_for_tasks(
        self,
        search_query,
        search_rate=1,
        max_tries=10,
        poll_rate=None,
        poll_timeout=None,
        must_succeed=True,
    ):
        """Search for tasks by specified search query and poll them to ensure that
        task has finished.

        :param search_query: Search query that will be passed to API call.
        :param search_rate: Delay between searches.
        :param max_tries: How many times search should be executed.
        :param poll_rate: Delay between the end of one task check-up and
            the start of the next check-up. Parameter for ``sat.api.ForemanTask.poll()`` method.
        :param poll_timeout: Maximum number of seconds to wait until timing out.
            Parameter for ``sat.api.ForemanTask.poll()`` method.
        :param must_succeed: Assert success result on finished task.
        :return: List of ``sat.api.ForemanTasks`` entities.
        :raises: ``AssertionError``. If not tasks were found until timeout.
        """
        for _ in range(max_tries):
            tasks = self.satellite.api.ForemanTask().search(query={'search': search_query})
            if tasks:
                for task in tasks:
                    task.poll(poll_rate=poll_rate, timeout=poll_timeout, must_succeed=must_succeed)
                break
            else:
                time.sleep(search_rate)
        else:
            raise AssertionError(f"No task was found using query '{search_query}'")
        return tasks

    def wait_for_sync(self, timeout=600, start_time=datetime.utcnow()):
        """Wait for capsule sync to finish and assert the sync task succeeded"""
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        logger.info(f"Waiting for capsule {self.hostname} sync to finish ...")
        sync_status = self.nailgun_capsule.content_get_sync()
        logger.info(f"Active tasks {sync_status['active_sync_tasks']}")
        assert (
            len(sync_status['active_sync_tasks'])
            or datetime.strptime(sync_status['last_sync_time'], '%Y-%m-%d %H:%M:%S UTC')
            > start_time
        )

        # Wait till capsule sync finishes and assert the sync task succeeded
        for task in sync_status['active_sync_tasks']:
            self.satellite.api.ForemanTask(id=task['id']).poll(timeout=timeout)
        sync_status = self.nailgun_capsule.content_get_sync()
        assert len(sync_status['last_failed_sync_tasks']) == 0

    def get_published_repo_url(self, org, prod, repo, lce=None, cv=None):
        """Forms url of a repo or CV published on a Satellite or Capsule.

        :param str org: organization label
        :param str prod: product label
        :param str repo: repository label
        :param str lce: lifecycle environment label
        :param str cv: content view label
        :return: url of the specific repo or CV
        """
        if lce and cv:
            return f'{self.url}/pulp/content/{org}/{lce}/{cv}/custom/{prod}/{repo}/'
        else:
            return f'{self.url}/pulp/content/{org}/Library/custom/{prod}/{repo}/'
