"""Robottelo configuration migrations

This module contains functions that are run after the configuration is loaded. Each function
should be named `migration_<YYMMDD>_<description>` and accept two parameters: `settings` and
`data`. `settings` is a `dynaconf` `Box` object containing the configuration. `data` is a
`dict` that can be used to store settings that will be merged with the rest of the settings.
The functions should not return anything.
"""

import warnings

from packaging.version import Version

from robottelo.enums import HostNetworkType
from robottelo.logging import logger


def migration_231129_deploy_workflow(settings, data):
    """Migrates {server,capsule}.deploy_workflow to {server,capsule}.deploy_workflows"""
    for product_type in ['server', 'capsule']:
        # If the product_type has a deploy_workflow and it is a string, and
        # it does not have a deploy_workflows set
        if (
            settings[product_type].get('deploy_workflow')
            and isinstance(settings[product_type].deploy_workflow, str)
            and not settings[product_type].get('deploy_workflows')
        ):
            sat_rhel_version = settings[product_type].version.rhel_version
            data[product_type] = {}
            # Set the deploy_workflows to a dict with product and os keys
            # Get the OS workflow from the content_host config
            data[product_type].deploy_workflows = {
                'product': settings[product_type].deploy_workflow,
                'os': settings.content_host[
                    f'rhel{Version(str(sat_rhel_version)).major}'
                ].vm.workflow,
            }
            logger.info(
                f'Migrated {product_type}.DEPLOY_WORKFLOW to {product_type}.DEPLOY_WORKFLOWS'
            )


def migration_241120_http_proxy_ipv6_url(settings, data):
    """Migrates server.http_proxy_ipv6_url to http_proxy.http_proxy_ipv6_url"""
    if (
        settings.server.get('http_proxy_ipv6_url')
        and isinstance(settings.server.http_proxy_ipv6_url, str)
        and not settings.http_proxy.get('http_proxy_ipv6_url')
    ):
        data.http_proxy = {}
        data.http_proxy.http_proxy_ipv6_url = settings.server.http_proxy_ipv6_url
        logger.info('Migrated SERVER.HTTP_PROXY_IPv6_URL to HTTP_PROXY.HTTP_PROXY_IPV6_URL')


def migration_250404_network_type(settings, data):
    """Migrates server.is_ipv6 to server.network_type"""
    if hasattr(settings.server, 'is_ipv6') and not settings.server.get('network_type'):
        warnings.warn(
            'The SERVER.IS_IPV6 setting is deprecated. Use SERVER.NETWORK_TYPE instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        n_type = HostNetworkType.IPV6 if settings.server.is_ipv6 else HostNetworkType.IPV4
        if not hasattr(data, 'server'):
            data.server = {}
        data.server.network_type = str(n_type)
        # Remove the old setting
        data.server.is_ipv6 = '@del'
        logger.info('Migrated SERVER.IS_IPV6 to SERVER.NETWORK_TYPE')
