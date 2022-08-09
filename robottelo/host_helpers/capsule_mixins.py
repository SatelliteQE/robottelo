import contextlib
import time

from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.logging import logger


class CapsuleInfo:
    """Miscellaneous Capsule helper methods"""

    @contextlib.contextmanager
    def default_url_on_new_port(self, oldport, newport):
        """Creates context where the default capsule is forwarded on a new port

        :param int oldport: Port to be forwarded.
        :param int newport: New port to be used to forward `oldport`.

        :return: A string containing the new capsule URL with port.
        :rtype: str

        """
        pre_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
        with self.session.shell() as channel:
            # if ncat isn't backgrounded, it prevents the channel from closing
            command = f'ncat -kl -p {newport} -c "ncat {self.hostname} {oldport}" &'
            logger.debug(f'Creating tunnel: {command}')
            channel.send(command)
            post_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
            ncat_pid = set(post_ncat_procs).difference(set(pre_ncat_procs))
            if not len(ncat_pid):
                stderr = channel.get_exit_status()[1]
                logger.debug(f'Tunnel failed: {stderr}')
                # Something failed, so raise an exception.
                raise CapsuleTunnelError(f'Starting ncat failed: {stderr}')
            forward_url = f'https://{self.hostname}:{newport}'
            logger.debug(f'Yielding capsule forward port url: {forward_url}')
            try:
                yield forward_url
            finally:
                logger.debug(f'Killing ncat pid: {ncat_pid}')
                self.execute(f'kill {ncat_pid.pop()}')

    def wait_for_tasks(
        self, search_query, search_rate=1, max_tries=10, poll_rate=None, poll_timeout=None
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
        :return: List of ``sat.api.ForemanTasks`` entities.
        :raises: ``AssertionError``. If not tasks were found until timeout.
        """
        for _ in range(max_tries):
            tasks = self.api.ForemanTask().search(query={'search': search_query})
            if tasks:
                for task in tasks:
                    task.poll(poll_rate=poll_rate, timeout=poll_timeout)
                break
            else:
                time.sleep(search_rate)
        else:
            raise AssertionError(f"No task was found using query '{search_query}'")
        return tasks
