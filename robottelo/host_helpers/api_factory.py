"""
It is not meant to be used directly, but as part of a robottelo.hosts.Satellite instance
example: my_satellite.api_factory.api_method()
"""
from contextlib import contextmanager

from fauxfactory import gen_string

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
