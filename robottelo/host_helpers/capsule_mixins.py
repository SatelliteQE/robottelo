import time

from robottelo.constants import PUPPET_CAPSULE_INSTALLER
from robottelo.constants import PUPPET_COMMON_INSTALLER_OPTS
from robottelo.utils.installer import InstallerCommand


class EnablePluginsCapsule:
    """Miscellaneous settings helper methods"""

    def enable_puppet_capsule(self):
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
            tasks = self.api.ForemanTask().search(query={'search': search_query})
            if tasks:
                for task in tasks:
                    task.poll(poll_rate=poll_rate, timeout=poll_timeout, must_succeed=must_succeed)
                break
            else:
                time.sleep(search_rate)
        else:
            raise AssertionError(f"No task was found using query '{search_query}'")
        return tasks
