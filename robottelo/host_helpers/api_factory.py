"""
It is not meant to be used directly, but as part of a robottelo.hosts.Satellite instance
example: my_satellite.api_factory.api_method()
"""
from contextlib import contextmanager

from fauxfactory import gen_string
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
