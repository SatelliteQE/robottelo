"""Helpers for Azure compute resource tests."""

import shlex

from robottelo.logging import logger


def diagnose_azurerm_ssh_port(sat_azure, azurermclient, vm_name):
    """Log whether the Satellite host can reach TCP port 22 on an Azure VM."""
    try:
        matching_vms = azurermclient.find_vms(name=vm_name)
        if not matching_vms:
            logger.warning('Azure SSH diagnostic: VM %s was not found', vm_name)
            return

        vm_ip = matching_vms[0].ip
        if not vm_ip:
            logger.warning('Azure SSH diagnostic: VM %s has no IP address', vm_name)
            return

        command = (
            "python3 -c 'import socket, sys; "
            "connection = socket.create_connection((sys.argv[1], 22), timeout=5); "
            "connection.close()' "
            f'{shlex.quote(str(vm_ip))}'
        )
        result = sat_azure.execute(command, timeout='15s')
        if result.status == 0:
            logger.warning(
                'Azure SSH diagnostic from Satellite: TCP/22 on VM %s (%s) is responding',
                vm_name,
                vm_ip,
            )
            return

        detail = (result.stderr or result.stdout).strip()
        logger.warning(
            'Azure SSH diagnostic from Satellite: TCP/22 probe for VM %s (%s) failed: %s',
            vm_name,
            vm_ip,
            detail or f'exit status {result.status}',
        )
    except Exception as error:
        logger.warning('Unable to collect Azure SSH diagnostics for VM %s: %s', vm_name, error)
