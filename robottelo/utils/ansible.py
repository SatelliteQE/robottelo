"""Settle Ansible role imports before cleaning up test resources."""

from contextlib import ExitStack

from wait_for import TimedOutError, wait_for

from robottelo.exceptions import CLIError


class AnsibleSyncTasks(list):
    """Retain task IDs and recover lost replies using a pre-submission task snapshot."""

    def __init__(self, satellite, role_names, proxy_id):
        super().__init__()
        self.satellite = satellite
        self.role_names = set(role_names)
        self.proxy_id = proxy_id
        self.previous = {task['id'] for task in self._tasks()}

    def _tasks(self):
        tasks = []
        page = 1
        while True:
            results = self.satellite.api.ForemanTask().search_json(
                query={
                    'search': 'label = SyncRolesAndVariables',
                    'per_page': 100,
                    'page': page,
                    'order': 'started_at ASC',
                }
            )['results']
            tasks.extend(results)
            if len(results) < 100:
                return tasks
            page += 1

    def discover(self):
        """Record new sync tasks for this proxy and these roles, including stopped jobs."""
        for task in self._tasks():
            if task['id'] in self.previous or task['id'] in self:
                continue
            # ActiveJob serializes (changed_roles, proxy) as these two arguments.
            arguments = task.get('input')
            if not isinstance(arguments, list) or len(arguments) != 2:
                raise CLIError(f'Cannot identify Ansible sync task {task["id"]}: unknown input')
            changed, proxy = arguments
            if proxy.get('_aj_globalid') != f'gid://foreman/SmartProxy/{self.proxy_id}':
                continue
            # ActiveJob adds metadata keys alongside the role-name entries.
            names = {
                role['name']
                for kind in ('new', 'old', 'obsolete')
                for role in changed.get(kind, {}).values()
                if isinstance(role, dict) and 'name' in role
            }
            if names and names <= self.role_names:
                self.append(task['id'])


def cleanup_ansible_role(satellite, role_name, task_ids=(), timeout=180):
    """Clean up a single test role after settling its imports."""
    cleanup_ansible_roles(satellite, [role_name], task_ids, timeout)


def cleanup_ansible_roles(satellite, role_names, task_ids=(), timeout=180):
    """Discover uncertain submissions, settle their tasks, then delete the requested roles."""
    if isinstance(task_ids, AnsibleSyncTasks):
        task_ids.discover()
    for task_id in task_ids:
        task = satellite.api.ForemanTask(id=task_id)

        def wait_for_stop(task=task, task_id=task_id):
            wait_for(
                lambda: task.read().state == 'stopped',
                timeout=timeout,
                delay=2,
                text=f'Ansible role sync task {task_id} to stop',
            )

        try:
            wait_for_stop()
        except TimedOutError:
            task.bulk_cancel(data={'task_ids': [task_id]})
            wait_for_stop()

    with ExitStack() as cleanup:
        for role_name in role_names:
            cleanup.callback(_delete_ansible_role, satellite, role_name)


def _delete_ansible_role(satellite, role_name):
    role_search = {'search': f'name="{role_name}"'}
    if not satellite.cli.Ansible.roles_list(role_search):
        return
    satellite.cli.Ansible.roles_delete({'name': role_name})
