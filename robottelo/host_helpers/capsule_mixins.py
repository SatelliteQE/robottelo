import time


class CapsuleInfo:
    """Miscellaneous Capsule helper methods"""

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
