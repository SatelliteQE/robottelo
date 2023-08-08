"""
It is not meant to be used directly, but as part of a robottelo.hosts.Satellite instance
example: my_satellite.api_factory.api_method()
"""
import time
from contextlib import contextmanager

from fauxfactory import gen_string
from nailgun.client import request
from requests import HTTPError

from robottelo.config import settings


class APIFactory:
    """This class is part of a mixin and not to be used directly. See robottelo.hosts.Satellite"""

    def __init__(self, satellite):
        self._satellite = satellite

    def make_http_proxy(self, org, http_proxy_type):
        """
        Creates HTTP proxy.
        :param str org: Organization
        :param str http_proxy_type: None, False, True
        """
        if http_proxy_type is False:
            return self._satellite.api.HTTPProxy(
                name=gen_string('alpha', 15),
                url=settings.http_proxy.un_auth_proxy_url,
                organization=[org.id],
            ).create()
        if http_proxy_type:
            return self._satellite.api.HTTPProxy(
                name=gen_string('alpha', 15),
                url=settings.http_proxy.auth_proxy_url,
                username=settings.http_proxy.username,
                password=settings.http_proxy.password,
                organization=[org.id],
            ).create()

    def enable_rhrepo_and_fetchid(
        self, basearch, org_id, product, repo, reposet, releasever=None, strict=False
    ):
        """Enable a RedHat Repository and fetches it's Id.

        :param str org_id: The organization Id.
        :param str product: The product name in which repository exists.
        :param str reposet: The reposet name in which repository exists.
        :param str repo: The repository name who's Id is to be fetched.
        :param str basearch: The architecture of the repository.
        :param str optional releasever: The releasever of the repository.
        :param bool optional strict: Raise exception if the reposet was already enabled.
        :return: Returns the repository Id.
        :rtype: str

        """
        product = self._satellite.api.Product(name=product, organization=org_id).search()[0]
        r_set = self._satellite.api.RepositorySet(name=reposet, product=product).search()[0]
        payload = {}
        if basearch is not None:
            payload['basearch'] = basearch
        if releasever is not None:
            payload['releasever'] = releasever
        payload['product_id'] = product.id
        try:
            r_set.enable(data=payload)
        except HTTPError as e:
            if (
                not strict
                and e.response.status_code == 409
                and 'repository is already enabled' in e.response.json()['displayMessage']
            ):
                pass
            else:
                raise
        result = self._satellite.api.Repository(name=repo).search(query={'organization_id': org_id})
        return result[0].id

    def update_vm_host_location(self, vm_client, location_id):
        """Update vm client host location.

        :param vm_client: A subscribed Virtual Machine client instance.
        :param location_id: The location id to update the vm_client host with.
        """
        self._satellite.api.Host(
            id=vm_client.nailgun_host.id, location=self._satellite.api.Location(id=location_id)
        ).update(['location'])

    @contextmanager
    def satellite_setting(self, key_val: str):
        """Context Manager to update the satellite setting and revert on exit

        :param key_val: The setting name and value in format `setting_name=new_value`
        """
        try:
            name, value = key_val.split('=')
            try:
                setting = self._satellite.api.Setting().search(
                    query={'search': f'name={name.strip()}'}
                )[0]
            except IndexError:
                raise KeyError(f'The setting {name} in not available in satellite.')
            old_value = setting.value
            setting.value = value.strip()
            setting.update({'value'})
            yield
        except Exception:
            raise
        finally:
            setting.value = old_value
            setting.update({'value'})

    def update_provisioning_template(self, name=None, old=None, new=None):
        """Update provisioning template content

        :param str name: template provisioning name
        :param str old: current content
        :param str new: replace content

        :return bool: True/False
        """
        self.temp = (
            self._satellite.api.ProvisioningTemplate()
            .search(query={'per_page': '1000', 'search': f'name="{name}"'})[0]
            .read()
        )
        if old in self.temp.template:
            with self.template_update(self.temp):
                self.temp.template = self.temp.template.replace(old, new, 1)
                update = self.temp.update(['template'])
            return new in update.template
        elif new in self.temp.template:
            return True
        else:
            raise ValueError(f'{old} does not exists in template {name}')

    def disable_syncplan(self, sync_plan):
        """
        Disable sync plans after a test to reduce distracting task events, logs,
        and load on Satellite.
        Note that only a Sync Plan with a repo would create a noticeable load.
        You can also create sync plans in a disabled state where it is unlikely to impact the test.
        """
        sync_plan.enabled = False
        sync_plan = sync_plan.update(['enabled'])
        assert sync_plan.enabled is False

    @contextmanager
    def template_update(self, temp):
        template = temp
        if template.locked:
            template.locked = False
            template.update(['locked'])
        yield
        if not template.locked:
            template.locked = True
            template.update(['locked'])

    def attach_custom_product_subscription(self, prod_name=None, host_name=None):
        """Attach custom product subscription to client host
        :param str prod_name: custom product name
        :param str host_name: client host name
        """
        host = self._satellite.api.Host().search(query={'search': f'{host_name}'})[0]
        product_subscription = self._satellite.api.Subscription().search(
            query={'search': f'name={prod_name}'}
        )[0]
        self._satellite.api.HostSubscription(host=host.id).add_subscriptions(
            data={'subscriptions': [{'id': product_subscription.id, 'quantity': 1}]}
        )

    def wait_for_errata_applicability_task(
        self, host_id, from_when, search_rate=1, max_tries=10, poll_rate=None, poll_timeout=15
    ):
        """Search the generate applicability task for given host and make sure it finishes

        :param int host_id: Content host ID of the host where we are regenerating applicability.
        :param int from_when: Timestamp (in UTC) to limit number of returned tasks to investigate.
        :param int search_rate: Delay between searches.
        :param int max_tries: How many times search should be executed.
        :param int poll_rate: Delay between the end of one task check-up and
                the start of the next check-up. Parameter for
                ``nailgun.entities.ForemanTask.poll()`` method.
        :param int poll_timeout: Maximum number of seconds to wait until timing out.
                Parameter for ``nailgun.entities.ForemanTask.poll()`` method.
        :return: Relevant errata applicability task.
        :raises: ``AssertionError``. If not tasks were found for given host until timeout.
        """
        assert isinstance(host_id, int), 'Param host_id have to be int'
        assert isinstance(from_when, int), 'Param from_when have to be int'
        now = int(time.time())
        assert from_when <= now, 'Param from_when have to be timestamp in the past'
        for _ in range(max_tries):
            now = int(time.time())
            max_age = now - from_when + 1
            search_query = (
                '( label = Actions::Katello::Host::GenerateApplicability OR label = '
                'Actions::Katello::Host::UploadPackageProfile ) AND started_at > "%s seconds ago"'
                % max_age
            )
            tasks = self._satellite.api.ForemanTask().search(query={'search': search_query})
            tasks_finished = 0
            for task in tasks:
                if (
                    task.label == 'Actions::Katello::Host::GenerateApplicability'
                    and host_id in task.input['host_ids']
                ):
                    task.poll(poll_rate=poll_rate, timeout=poll_timeout)
                    tasks_finished += 1
                elif (
                    task.label == 'Actions::Katello::Host::UploadPackageProfile'
                    and host_id == task.input['host']['id']
                ):
                    task.poll(poll_rate=poll_rate, timeout=poll_timeout)
                    tasks_finished += 1
            if tasks_finished > 0:
                break
            time.sleep(search_rate)
        else:
            raise AssertionError(
                f"No task was found using query '{search_query}' for host '{host_id}'"
            )

    def wait_for_syncplan_tasks(self, repo_backend_id=None, timeout=10, repo_name=None):
        """Search the pulp tasks and identify repositories sync tasks with
        specified name or backend_identifier

        :param repo_backend_id: The Backend ID for the repository to identify the
            repo in Pulp environment
        :param timeout: Value to decided how long to check for the Sync task
        :param repo_name: If repo_backend_id can not be passed, pass the repo_name
        """
        if repo_name:
            repo_backend_id = (
                self._satellite.api.Repository()
                .search(query={'search': f'name="{repo_name}"', 'per_page': '1000'})[0]
                .backend_identifier
            )
        # Fetch the Pulp password
        pulp_pass = self._satellite.execute(
            'grep "^default_password" /etc/pulp/server.conf | awk \'{print $2}\''
        ).stdout.splitlines()[0]
        # Set the Timeout value
        timeup = time.time() + int(timeout) * 60
        # Search Filter to filter out the task based on backend-id and sync action
        filtered_req = {
            'criteria': {
                'filters': {
                    'tags': {'$in': [f"pulp:repository:{repo_backend_id}"]},
                    'task_type': {'$in': ["pulp.server.managers.repo.sync.sync"]},
                }
            }
        }
        while True:
            if time.time() > timeup:
                raise self._satellite.api.APIResponseError(
                    f'Pulp task with repo_id {repo_backend_id} not found'
                )
            # Send request to pulp API to get the task info
            req = request(
                'POST',
                f'{self._satellite.url}/pulp/api/v2/tasks/search/',
                verify=False,
                auth=('admin', f'{pulp_pass}'),
                headers={'content-type': 'application/json'},
                data=filtered_req,
            )
            # Check Status code of response
            if req.status_code != 200:
                raise self._satellite.api.APIResponseError(
                    f'Pulp task with repo_id {repo_backend_id} not found'
                )
            # Check content of response
            # It is '[]' string for empty content when backend_identifier is wrong
            if len(req.content) > 2:
                if req.json()[0].get('state') in ['finished']:
                    return True
                elif req.json()[0].get('error'):
                    raise AssertionError(
                        f"Pulp task with repo_id {repo_backend_id} error or not found: "
                        f"'{req.json().get('error')}'"
                    )
            time.sleep(2)
