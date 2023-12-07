"""Robottelo configuration migrations

This module contains functions that are run after the configuration is loaded. Each function
should be named `migration_<YYMMDD>_<description>` and accept two parameters: `settings` and
`data`. `settings` is a `dynaconf` `Box` object containing the configuration. `data` is a
`dict` that can be used to store settings that will be merged with the rest of the settings.
The functions should not return anything.
"""

from packaging.version import Version

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
