"""
It is not meant to be used directly, but as part of a robottelo.hosts.Satellite instance
example: my_satellite.api_factory.api_method()
"""

from contextlib import contextmanager
from datetime import datetime
import time

from fauxfactory import gen_ipaddr, gen_mac, gen_string
from nailgun.client import request
from nailgun.entity_mixins import call_entity_method_with_timeout
from requests import HTTPError

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    REPO_TYPE,
)
from robottelo.host_helpers.repository_mixins import initiate_repo_helpers


class APIFactory:
    """This class is part of a mixin and not to be used directly. See robottelo.hosts.Satellite"""

    def __init__(self, satellite):
        self._satellite = satellite
        self.__dict__.update(initiate_repo_helpers(self._satellite))

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
        return None

    def cv_publish_promote(self, name=None, env_name=None, repo_id=None, org_id=None):
        """Create, publish and promote CV to selected environment"""
        if org_id is None:
            org_id = self._satellite.api.Organization().create().id
        # Create Life-Cycle content environment
        kwargs = {'name': env_name} if env_name is not None else {}
        lce = self._satellite.api.LifecycleEnvironment(organization=org_id, **kwargs).create()
        # Create content view(CV)
        kwargs = {'name': name} if name is not None else {}
        content_view = self._satellite.api.ContentView(organization=org_id, **kwargs).create()
        # Associate YUM repo to created CV
        if repo_id is not None:
            content_view.repository = [self._satellite.api.Repository(id=repo_id)]
            content_view = content_view.update(['repository'])
        # Publish content view
        content_view.publish()
        # Promote the content view version.
        content_view_version = content_view.read().version[0]
        content_view_version.promote(data={'environment_ids': lce.id})
        return content_view.read()

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

    def create_sync_custom_repo(
        self,
        org_id=None,
        product_name=None,
        repo_name=None,
        repo_url=None,
        repo_type=None,
        repo_unprotected=True,
        docker_upstream_name=None,
    ):
        """Create product/repo, sync it and returns repo_id"""
        if org_id is None:
            org_id = self._satellite.api.Organization().create().id
        product_name = product_name or gen_string('alpha')
        repo_name = repo_name or gen_string('alpha')
        # Creates new product and repository via API's
        product = self._satellite.api.Product(name=product_name, organization=org_id).create()
        repo = self._satellite.api.Repository(
            name=repo_name,
            url=repo_url or settings.repos.yum_1.url,
            content_type=repo_type or REPO_TYPE['yum'],
            product=product,
            unprotected=repo_unprotected,
            docker_upstream_name=docker_upstream_name,
        ).create()
        # Sync repository
        self._satellite.api.Repository(id=repo.id).sync()
        return repo.id

    def enable_sync_redhat_repo(self, rh_repo, org_id, timeout=1500):
        """Enable the RedHat repo, sync it and returns repo_id"""
        # Enable RH repo and fetch repository_id
        repo_id = self.enable_rhrepo_and_fetchid(
            basearch=rh_repo.get('basearch', rh_repo.get('arch', DEFAULT_ARCHITECTURE)),
            org_id=org_id,
            product=rh_repo['product'],
            repo=rh_repo['name'],
            reposet=rh_repo['reposet'],
            releasever=rh_repo['releasever'],
        )
        # Sync repository
        call_entity_method_with_timeout(
            self._satellite.api.Repository(id=repo_id).sync, timeout=timeout
        )
        return repo_id

    def one_to_one_names(self, name):
        """Generate the names Satellite might use for a one to one field.

        Example of usage::

            >>> one_to_one_names('person') == {'person_name', 'person_id'}
            True

        :param name: A field name.
        :return: A set including both ``name`` and variations on ``name``.

        """
        return {f'{name}_name', f'{name}_id'}

    def create_role_permissions(
        self, role, permissions_types_names, search=None
    ):  # pragma: no cover
        """Create role permissions found in dict permissions_types_names.

        :param role: nailgun.entities.Role
        :param permissions_types_names: a dict containing resource types
            and permission names to add to the role.
        :param search: string that contains search criteria that should be applied
            to the filter

              example usage::

               permissions_types_names = {
                   None: ['access_dashboard'],
                   'Organization': ['view_organizations'],
                   'Location': ['view_locations'],
                   'Katello::KTEnvironment': [
                       'view_lifecycle_environments',
                       'edit_lifecycle_environments',
                       'promote_or_remove_content_views_to_environments'
                   ]
               }
               role = entities.Role(name='example_role_name').create()
               create_role_permissions(
                   role,
                   permissions_types_names,
                   'name = {0}'.format(lce.name)
               )
        """
        for resource_type, permissions_name in permissions_types_names.items():
            if resource_type is None:
                permissions_entities = []
                for name in permissions_name:
                    result = self._satellite.api.Permission().search(
                        query={'search': f'name="{name}"'}
                    )
                    if not result:
                        raise self._satellite.api.APIResponseError(f'permission "{name}" not found')
                    if len(result) > 1:
                        raise self._satellite.api.APIResponseError(
                            f'found more than one entity for permission "{name}"'
                        )
                    entity_permission = result[0]
                    if entity_permission.name != name:
                        raise self._satellite.api.APIResponseError(
                            'the returned permission is different from the'
                            f' requested one "{entity_permission.name} != {name}"'
                        )
                    permissions_entities.append(entity_permission)
            else:
                if not permissions_name:
                    raise ValueError(
                        f'resource type "{resource_type}" empty. You must select at'
                        ' least one permission'
                    )

                resource_type_permissions_entities = self._satellite.api.Permission().search(
                    query={'per_page': '350', 'search': f'resource_type="{resource_type}"'}
                )
                if not resource_type_permissions_entities:
                    raise self._satellite.api.APIResponseError(
                        f'resource type "{resource_type}" permissions not found'
                    )

                permissions_entities = [
                    entity
                    for entity in resource_type_permissions_entities
                    if entity.name in permissions_name
                ]
                # ensure that all the requested permissions entities where
                # retrieved
                permissions_entities_names = {entity.name for entity in permissions_entities}
                not_found_names = set(permissions_name).difference(permissions_entities_names)
                if not_found_names:
                    raise self._satellite.api.APIResponseError(
                        f'permissions names entities not found "{not_found_names}"'
                    )
            self._satellite.api.Filter(
                permission=permissions_entities, role=role, search=search
            ).create()

    def create_discovered_host(self, name=None, ip_address=None, mac_address=None, options=None):
        """Creates a discovered host.

        :param str name: Name of discovered host.
        :param str ip_address: A valid ip address.
        :param str mac_address: A valid mac address.
        :param dict options: additional facts to add to discovered host
        :return: dict of ``entities.DiscoveredHost`` facts.
        """
        if name is None:
            name = gen_string('alpha')
        if ip_address is None:
            ip_address = gen_ipaddr()
        if mac_address is None:
            mac_address = gen_mac(multicast=False)
        if options is None:
            options = {}
        facts = {
            'name': name,
            'discovery_bootip': ip_address,
            'discovery_bootif': mac_address,
            'interfaces': 'eth0',
            'ipaddress': ip_address,
            'ipaddress_eth0': ip_address,
            'macaddress': mac_address,
            'macaddress_eth0': mac_address,
        }
        facts.update(options)
        return self._satellite.api.DiscoveredHost().facts(json={'facts': facts})

    def update_vm_host_location(self, vm_client, location_id):
        """Update vm client host location.

        :param vm_client: A subscribed Virtual Machine client instance.
        :param location_id: The location id to update the vm_client host with.
        """
        self._satellite.api.Host(
            id=vm_client.nailgun_host.id, location=self._satellite.api.Location(id=location_id)
        ).update(['location'])

    def check_create_os_with_title(self, os_title):
        """Check if the OS is present, if not create the required OS

        :param os_title: OS title to check, and create (like: RedHat 7.5)
        :return: Created or found OS
        """
        # Check if OS that image needs is present or no, If not create the OS
        result = self._satellite.api.OperatingSystem().search(
            query={'search': f'title="{os_title}"'}
        )
        if result:
            os = result[0]
        else:
            os_name, _, os_version = os_title.partition(' ')
            os_version_major, os_version_minor = os_version.split('.')
            os = self._satellite.api.OperatingSystem(
                name=os_name, major=os_version_major, minor=os_version_minor
            ).create()
        return os

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
            except IndexError as err:
                raise KeyError(f'The setting {name} in not available in satellite.') from err
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
        if new in self.temp.template:
            return True
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

    def wait_for_errata_applicability_task(
        self,
        host_id,
        from_when,
        search_rate=1,
        max_tries=10,
        poll_rate=None,
        poll_timeout=15,
    ):
        """Search the generate applicability task for given host and make sure it finishes

        :param int host_id: Content host ID of the host where we are regenerating applicability.
        :param int from_when: Epoch Time (seconds in UTC) to limit number of returned tasks to investigate.
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
        assert from_when <= now, 'Param from_when have to be epoch time in the past'
        for _ in range(max_tries):
            now = int(time.time())
            # Format epoch time for search, one second prior margin of safety
            timestamp = datetime.fromtimestamp(from_when - 1).strftime('%m-%d-%Y %H:%M:%S')
            # Long format to match search: ex. 'January 03, 2024 at 03:08:08 PM'
            long_format = datetime.strptime(timestamp, '%m-%d-%Y %H:%M:%S').strftime(
                '%B %d, %Y at %I:%M:%S %p'
            )
            search_query = (
                '( label = Actions::Katello::Applicability::Hosts::BulkGenerate OR'
                ' label = Actions::Katello::Host::UploadPackageProfile ) AND'
                f' started_at >= "{long_format}" '
            )
            tasks = self._satellite.api.ForemanTask().search(query={'search': search_query})
            tasks_finished = 0
            for task in tasks:
                if (
                    task.label == 'Actions::Katello::Applicability::Hosts::BulkGenerate'
                    and 'host_ids' in task.input
                    and host_id in task.input['host_ids']
                ) or (
                    task.label == 'Actions::Katello::Host::UploadPackageProfile'
                    and 'host' in task.input
                    and host_id == task.input['host']['id']
                ):
                    task.poll(poll_rate=poll_rate, timeout=poll_timeout)
                    tasks_finished += 1
            if tasks_finished > 0:
                break
            time.sleep(search_rate)
        else:
            raise AssertionError(
                f'No task was found using query " {search_query} " for host id: {host_id}'
            )

    def register_host_and_needed_setup(
        self,
        client,
        organization,
        activation_key,
        environment,
        content_view,
        enable_repos=False,
        rex_key=False,
        force=False,
        loc=None,
    ):
        """Helper will setup desired entities to host content. Then, register the
        host client to the entities, using associated activation-key.

        Attempt to make needed associations between detached entities.
        Add desired repos to the content-view prior to calling this helper.

        Or, add them to content-view after calling, then publish/promote.
        The host will be registered to location: None (visible to all locations).

        param client : instance, required
            An instance of RHEL content host to register.
        param enable_repos : bool, optional
            Enable all available repos on the client after registration? Default is False.
            Be sure to enable any repo(s) for the client after calling this method.
        param rex_key : bool, optional
            Add a Remote Execution Key to the client for satellite? Default is False.
        param force : bool, optional
            Force registration of the client to bypass? Default is False.
            A reused fixture content host will fail if already registered.
        param loc : instance, optional
            Pass a location to limit host visibility. Default is None,
            making the client available to all locations.

        Required arguments below, can be any of the following type:
        int: pass id of the entity to be read
        str: pass name of the entity to be searched
        entity: pass an entity instance

        param organization : int, str, or entity
            Pass an Organization instance, name, or id to use.
        param activation_key : int, str, or entity
            Pass an Activation-Key instance, name, or id.
        param environment : int, str, or entity
            Pass a Lifecycle-Environment instance, name, or id.
            Example: can pass string name 'Library'.
        param content_view : int, str, or entity
            Pass a Content-View instance, name, or id.
            Example: can pass string name 'Default Organization View'.

        Note: The Default Organization View cannot be published, promoted, edited etc,
            but you can register the client to it. Use the 'Library' environment.

        Steps:
            1. Get needed entities from arguments (id, name, or instance). Read all as instance.
            2. Publish the content-view if no versions exist or needs_publish.
            3. Promote the newest content-view-version if not in the environment already. Skip for 'Library'.
            4. Assign environment and content-view to the activation-key if not associated.
            5. If desired, enable all repositories from content-view for activation-key.
            6. Register the host with options, using the activation-key associated with the content.
            7. Check host was registered, identity matches passed entities.

        Return: dictionary containing the following entries
            if succeeded:
                result: 'success'
                client: registered host client
                organization: entities['Organization']
                activation_key: entities['ActivationKey']
                environment: entities['LifecycleEnvironment']
                content_view: entities['ContentView']

            if failed:
                result: 'error'
                client: None, unless registration was successful
                message: Details of the failure encountered
        """

        method_error = {
            'result': 'error',
            'client': None,
            'message': None,
        }
        entities = {
            'Organization': organization,
            'ActivationKey': activation_key,
            'LifecycleEnvironment': environment,
            'ContentView': content_view,
        }
        if not hasattr(client, 'hostname'):
            method_error['message'] = (
                'Argument "client" must be instance, with attribute "hostname".'
            )
            return method_error
        # for entity arguments matched to above params:
        # fetch entity instance on satellite,
        # from given id or name, else read passed argument as an instance.
        for entity, value in entities.items():
            param = None
            # passed int for entity, try to read by id
            if isinstance(value, int):
                # equivalent: _satellite_.api.{KEY}(id=VALUE).read()
                param = getattr(self._satellite.api, entity)(id=value).read()
            # passed str, search for entity by name
            elif isinstance(value, str):
                search_query = f'name="{value}"'
                if entity == 'Organization':
                    # search for org name itself, will be just scoped to satellite
                    # equivalent: _satellite_.api.{KEY}().search(...name={VALUE})
                    result = getattr(self._satellite.api, entity)().search(
                        query={'search': search_query}
                    )
                else:
                    # search of non-org entity by name, will be scoped to organization
                    result = getattr(self._satellite.api, entity)(
                        organization=entities['Organization']
                    ).search(query={'search': search_query})
                if not len(result) > 0:
                    method_error['message'] = (
                        f'Could not find {entity} name: {value}, by search query: "{search_query}"'
                    )
                    return method_error
                param = result[0]
            # did not pass int (id) or str (name), must be readable entity instance
            else:
                if not hasattr(value, 'id'):
                    method_error['message'] = (
                        f'Passed entity {entity}, has no attribute id:\n{value}'
                    )
                    return method_error
                param = value
            # updated param, should now be only an entity isntance
            if not hasattr(param, 'id'):
                method_error['message'] = (
                    f'Did not get readable instance from parameter on {self._satellite.hostname}:'
                    f' Param:{entity}:\n{value}'
                )
                return method_error
            # entity found, read updated instance into dictionary
            entities[entity] = param.read()

        if (  # publish a content-view-version if none exist, or needs_publish is True
            len(entities['ContentView'].version) == 0
            or entities['ContentView'].needs_publish is True
        ):
            entities['ContentView'].publish()
            # read updated entitites after modifying CV
            entities = {k: v.read() for k, v in entities.items()}

        # promote to non-Library env if not already present:
        # skip for 'Library' env selected or passed arg,
        # any published version(s) will already be in Library.
        if all(
            [
                environment != 'Library',
                entities['LifecycleEnvironment'].name != 'Library',
                entities['LifecycleEnvironment'] not in entities['ContentView'].environment,
            ]
        ):
            # promote newest version by id
            entities['ContentView'].version.sort(key=lambda version: version.id)
            entities['ContentView'].version[-1].promote(
                data={'environment_ids': entities['LifecycleEnvironment'].id}
            )
            # updated entities after promoting
            entities = {k: v.read() for k, v in entities.items()}

        if (  # assign env to ak if not present
            entities['ActivationKey'].environment is None
            or entities['ActivationKey'].environment.id != entities['LifecycleEnvironment'].id
        ):
            entities['ActivationKey'].environment = entities['LifecycleEnvironment']
            entities['ActivationKey'].update(['environment'])
            entities = {k: v.read() for k, v in entities.items()}
        if (  # assign cv to ak if not present
            entities['ActivationKey'].content_view is None
            or entities['ActivationKey'].content_view.id != entities['ContentView'].id
        ):
            entities['ActivationKey'].content_view = entities['ContentView']
            entities['ActivationKey'].update(['content_view'])

        entities = {k: v.read() for k, v in entities.items()}
        if enable_repos:
            repositories = entities['ContentView'].repository
            if len(repositories) < 1:
                method_error['message'] = (
                    f' Cannot enable repositories for clients activation-key: {entities["ActivationKey"].name}'
                    f' There are no repositories added to the content-view: {entities["ContentView"].name}.'
                )
                return method_error
            for repo in repositories:
                # fetch content-label for any repo in cv
                repo_content_label = self._satellite.cli.Repository.info(
                    {
                        'name': repo.read().name,
                        'organization-id': entities['Organization'].id,
                        'product': repo.read().product.read().name,
                    }
                )['content-label']
                # override the repository to enabled for ak
                self._satellite.cli.ActivationKey.content_override(
                    {
                        'content-label': repo_content_label,
                        'id': entities['ActivationKey'].id,
                        'organization-id': entities['Organization'].id,
                        'value': int(True),
                    }
                )

        # register with now setup entities, using ak
        result = client.register(
            activation_keys=entities['ActivationKey'].name,
            target=self._satellite,
            org=entities['Organization'],
            setup_remote_execution_pull=rex_key,
            force=force,
            loc=loc,
        )
        if result.status != 0:
            method_error['message'] = (
                f'Failed to register the host: {client.hostname}.\n{result.stderr}'
            )
            return method_error

        # check identity of now registered client, matches expected entities
        if not all(
            [
                client.subscribed,
                client.identity['registered_to'] == self._satellite.hostname,
                client.identity['org_name'] == entities['Organization'].name,
                client.identity['environment_name']
                == (f'{entities["LifecycleEnvironment"].name}/{entities["ContentView"].name}'),
            ]
        ):
            method_error['client'] = client
            method_error['message'] = (
                f'Registered client identity field(s) do not match expected:\n{client.identity}'
            )
            return method_error

        entities = {k: v.read() for k, v in entities.items()}
        return (  # dict containing registered host client, and updated entities
            {
                'result': 'success',
                'client': client,
                'organization': entities['Organization'],
                'activation_key': entities['ActivationKey'],
                'environment': entities['LifecycleEnvironment'],
                'content_view': entities['ContentView'],
            }
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
                if req.json()[0].get('error'):
                    raise AssertionError(
                        f"Pulp task with repo_id {repo_backend_id} error or not found: "
                        f"'{req.json().get('error')}'"
                    )
            time.sleep(2)
