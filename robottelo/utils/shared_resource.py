"""Allow multiple processes to communicate status on a single shared resource.

This is useful for cases where multiple processes need to wait for all other processes to be ready
before continuing with some common action. The most common use case in this framework will likely
be to wait for all pre-upgrade setups to be ready before performing the upgrade.

The system works by creating a file in /tmp with the name of the resource. This is a common file
where each process can communicate its status. The first process to register will be the main
watcher. The main watcher will wait for all other processes to be ready, then perform the action.
If the main actor fails to complete the action, and the action is recoverable, another process
will take over as the main watcher and attempt to perform the action. If the action is not
recoverable, the main watcher will fail and release all other processes.

It is recommended to use this class as a context manager, as it will automatically register and
report when the process is done.

Example:
    >>> with SharedResource("target_sat.hostname", upgrade_action, **upgrade_kwargs) as resource:
    ...     # Do pre-upgrade setup steps
    ...     resource.ready()  # tell the other processes that we are ready
    ...     yield target_sat  # give the upgraded satellite to the test
    ...     # Do post-upgrade cleanup steps if any
"""

import datetime
import json
import os
from pathlib import Path
import time
from uuid import uuid4

from broker.helpers import FileLock
from wait_for import wait_for

from robottelo.config import settings


class SharedResourceError(Exception):
    """An exception class for SharedResource errors."""


class SharedResource:
    """A class representing a shared resource.

    Attributes:
        action (function): The function to be executed when the resource is ready.
        action_args (tuple): The arguments to be passed to the action function.
        action_kwargs (dict): The keyword arguments to be passed to the action function.
        action_is_recoverable (bool): Whether the action is recoverable or not.
        id (str): The unique identifier of the shared resource.
        resource_file (Path): The path to the file representing the shared resource.
        is_main (bool): Whether the current instance is the main watcher or not.
        is_recovering (bool): Whether the current instance is recovering from an error or not.
    """

    def __init__(
        self,
        resource_name,
        action,
        *action_args,
        action_validator=None,
        retries=3,
        delay=300,
        **action_kwargs,
    ):
        """Initializes a new instance of the SharedResource class.

        Args:
            resource_name (str): The name of the shared resource.
            action (function): The function to be executed when the resource is ready.
            action_args (tuple): The arguments to be passed to the action function.
            action_validator (function): The function to validate the action results.
            action_kwargs (dict): The keyword arguments to be passed to the action function.
        """
        self.resource_file = Path(f"/tmp/{resource_name}.shared")
        self.lock_file = FileLock(self.resource_file)
        self.id = str(uuid4().fields[-1])
        self.action = action
        self.action_validator = action_validator
        self.action_is_recoverable = action_kwargs.pop("action_is_recoverable", False)
        self.action_args = action_args
        self.action_kwargs = action_kwargs
        self.is_recovering = False
        self.retries = retries
        self.delay = delay

    def log(message, level="DEBUG"):
        """Pytest has a limitation to use logging.logger from conftest.py
        so we need to emulate the logger by std-out the output
        """
        now = datetime.datetime.now()
        full_message = "{date} - SHARED_RESOURCE - {level} - {message}\n".format(
            date=now.strftime("%Y-%m-%d %H:%M:%S"), level=level, message=message
        )
        print(full_message)  # noqa
        with open(f'logs/robottelo_{os.environ.get("PYTEST_XDIST_WORKER")}.log', 'a') as log_file:
            log_file.write(full_message)

    def _update_status(self, status):
        """Updates the status of the shared resource.

        Args:
            status (str): The new status of the shared resource.
        """
        with self.lock_file:
            curr_data = json.loads(self.resource_file.read_text())
            curr_data["statuses"][self.id] = status
            self.log(f"Updating watcher status to {status}")
            self.resource_file.write_text(json.dumps(curr_data, indent=4))

    def _update_main_status(self, status):
        """Updates the main status of the shared resource.

        Args:
            status (str): The new main status of the shared resource.
        """
        with self.lock_file:
            curr_data = json.loads(self.resource_file.read_text())
            curr_data["main_status"] = status
            self.resource_file.write_text(json.dumps(curr_data, indent=4))

    def _check_all_status(self, status):
        """Checks if all watchers have the specified status.

        Args:
            status (str): The status to check for.

        Returns:
            bool: True if all watchers have the specified status, False otherwise.
        """
        with self.lock_file:
            curr_data = json.loads(self.resource_file.read_text())
            for watcher_id in curr_data["watchers"]:
                if curr_data["statuses"].get(watcher_id) != status:
                    return False
            return True

    def _wait_for_status(self, status):
        """Waits until all watchers have the specified status.

        Args:
            status (str): The status to wait for.
        """
        while not self._check_all_status(status):
            if status == "done":
                self.log("Main worker still waiting for all workers to report status 'done'.")
            time.sleep(1)

    def _wait_for_main_watcher(self):
        """Waits for the main watcher to finish."""
        while True:
            curr_data = json.loads(self.resource_file.read_text())
            if curr_data["main_status"] == "error":
                raise Exception(f"Error in main watcher: {curr_data['main_watcher']}")
            if curr_data["main_status"] == "action_error":
                self._try_take_over()
            elif curr_data["main_status"] != "done":
                time.sleep(settings.robottelo.shared_resource_wait)
            else:
                self.log("Main status now done, breaking wait loop")
                break

    def _try_take_over(self):
        """Tries to take over as the main watcher."""
        with self.lock_file:
            curr_data = json.loads(self.resource_file.read_text())
            if curr_data["main_status"] in ("action_error", "error"):
                curr_data["main_status"] = "recovering"
                curr_data["main_watcher"] = self.id
                self.resource_file.write_text(json.dumps(curr_data, indent=4))
                self.is_main = True
                self.is_recovering = True
        self.wait()

    def register(self):
        """Registers the current process as a watcher."""
        with self.lock_file:
            if self.resource_file.exists():
                curr_data = json.loads(self.resource_file.read_text())
                self.is_main = False
            else:  # First watcher to register, becomes the main watcher, and creates the file
                curr_data = {
                    "watchers": [],
                    "statuses": {},
                    "main_watcher": self.id,
                    "main_status": "waiting",
                }
                self.is_main = True
            curr_data["watchers"].append(self.id)
            curr_data["statuses"][self.id] = "pending"
            self.resource_file.write_text(json.dumps(curr_data, indent=4))

    def unregister(self):
        """Unregisters the current process as a watcher."""
        self.log(f"Unregistering {os.environ.get('PYTEST_XDIST_WORKER')}")
        with self.lock_file:
            curr_data = json.loads(self.resource_file.read_text())
            self.log("Removing watcher ID from resource file")
            curr_data["watchers"].remove(self.id)
            del curr_data["statuses"][self.id]
            self.log("Writing new resource file")
            self.resource_file.write_text(json.dumps(curr_data, indent=4))

    def ready(self):
        """Marks the current process as ready to perform the action."""
        self._update_status("ready")
        self.wait()

    def done(self):
        """Marks the current process as done performing post actions."""
        self._update_status("done")

    def act(self):
        """Attempt to perform the action."""
        try:
            wait_for(
                lambda: self._perform_action_with_validation(),
                timeout=self.retries * self.delay,
                delay=self.delay,
            )
        except Exception as err:
            if not self.action_is_recoverable:
                self._update_main_status("error")
                self.resource_file.unlink()
                raise SharedResourceError('Main worker failed during action') from err
            self._update_main_status('action_error')
            raise SharedResourceError('Recoverable failures in main worker') from err

    def _perform_action_with_validation(self):
        """Helper function to run the action and its validation."""
        result = self.action(*self.action_args, **self.action_kwargs)
        # If the action_validator is a callable, use it to validate the result
        if callable(self.action_validator) and not self.action_validator(result):
            raise SharedResourceError(f"Action validation failed for {self.action} with {result=}")
        return result

    def wait(self):
        """Top-level wait function, separating behavior between main and non-main watchers."""
        if self.is_main and not (self.is_recovering and not self.action_is_recoverable):
            self._wait_for_status("ready")
            self._update_main_status("acting")
            self.act()
            self._update_main_status("done")
        else:
            self._wait_for_main_watcher()

    def __enter__(self):
        """Registers the current process as a watcher and returns the instance."""
        self.register()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Marks the current process as done and updates the main watcher if needed."""
        try:
            self.unregister()
        except Exception as e:
            self.log(
                f'WARNING: Failed to unregister watcher '
                f'(resource: {getattr(self, "resource_name", "unknown")}, '
                f'watcher ID: {getattr(self, "watcher_id", "unknown")}): {e}'
            )

        if exc_type is FileNotFoundError:
            self.log(
                f'{os.environ.get("PYTEST_XDIST_WORKER")} did not find resource file. has it already been deleted?'
            )
            raise exc_value
        if exc_type is None:
            self.log('Setting status to done')
            self.done()
            if self.is_main:
                self._wait_for_status("done")
                self.log("All workers done, removing resource file")
                self.resource_file.unlink()
        else:
            self._update_status("error")
            if self.is_main:
                if self._check_all_status("error"):
                    # All have failed, delete the file
                    self.log("All workers FAILED, removing resource file")
                    self.resource_file.unlink()
                else:
                    self.log("Setting main status to ERROR")
                    self._update_main_status("error")
            raise exc_value
