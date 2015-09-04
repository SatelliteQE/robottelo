"""Test utilities for writing Candlepin tests

Part of functionalities of Candlepin are defined in this module
and have utilities of single register by activation-key, single
register and attach, single subscription deletion.

"""
import logging
import requests
import time

from robottelo.common import conf, ssh
from robottelo.common.helpers import get_server_credentials, get_server_url
from urlparse import urljoin

LOGGER = logging.getLogger(__name__)


class Candlepin(object):
    """Measures performance of RH Satellite 6

    Candlepin Subscription functionality

    """

    # parameters for Candlepin Authentication
    username = conf.properties['foreman.admin.username']
    password = conf.properties['foreman.admin.password']
    serverhost = conf.properties['main.server.hostname']

    @staticmethod
    def get_real_time(result):
        """Parse stderr and extract out real time value

        :param str result: Standard Error
        :return: The real timing value

        """
        real_time = [
            real
            for real in result.split('\n')
            if real.startswith('real')
        ]
        return float(real_time[0].split(' ')[1])

    @classmethod
    def single_register_activation_key(cls, ak_name, default_org, vm_ip):
        """Subscribe VM to Satellite by Register + ActivationKey"""

        # note: must create ssh keys for vm if running on local
        result = ssh.command('subscription-manager clean', hostname=vm_ip)
        result = ssh.command(
            'time -p subscription-manager register --activationkey={0} '
            '--org={1}'.format(ak_name, default_org),
            hostname=vm_ip
        )

        if result.return_code != 0:
            LOGGER.error('Fail to subscribe {} by ak!'.format(vm_ip))
        else:
            LOGGER.info('Subscribe client {} successfully'.format(vm_ip))
        return cls.get_real_time(result.stderr)

    @classmethod
    def single_register_attach(cls, sub_id, default_org, environment, vm_ip):
        """Subscribe VM to Satellite by Register + Attach"""
        ssh.command('subscription-manager clean', hostname=vm_ip)

        time_reg = cls.sub_mgr_register_authentication(
            default_org, environment, vm_ip)

        time_att = cls.sub_mgr_attach(sub_id, vm_ip)
        return (time_reg, time_att)

    @classmethod
    def sub_mgr_register_authentication(cls, default_org, environment, vm_ip):
        """subscription-manager register -u -p --org --environment"""
        result = ssh.command(
            'time -p subscription-manager register --username={0} '
            '--password={1} '
            '--org={2} '
            '--environment={3}'
            .format(cls.username, cls.password, default_org, environment),
            hostname=vm_ip
        )

        if result.return_code != 0:
            LOGGER.error(
                'Fail to register client {} by sub-mgr!'.format(vm_ip)
            )
        else:
            LOGGER.info('Register client {} successfully'.format(vm_ip))
        return cls.get_real_time(result.stderr)

    @classmethod
    def sub_mgr_attach(cls, pool_id, vm_ip):
        """subscription-manager attach --pool=pool_id"""
        result = ssh.command(
            'time -p subscription-manager attach --pool={}'.format(pool_id),
            hostname=vm_ip
        )

        if result.return_code != 0:
            LOGGER.error('Fail to attach client {}'.format(vm_ip))
        else:
            LOGGER.info('Attach client {} successfully'.format(vm_ip))
        return cls.get_real_time(result.stderr)

    @classmethod
    def single_delete(cls, uuid, thread_id):
        """Delete system from subscription"""
        start = time.time()
        response = requests.delete(
            urljoin(get_server_url(), '/katello/api/systems/{0}'.format(uuid)),
            auth=get_server_credentials(),
            verify=False
        )

        if response.status_code != 204:
            LOGGER.error(
                'Fail to delete {0} on thread-{1}!'.format(uuid, thread_id)
            )
            LOGGER.error(response.content)
        else:
            LOGGER.info(
                "Delete {0} on thread-{1} successful!".format(uuid, thread_id)
            )
        end = time.time()
        LOGGER.info('real  {}s'.format(end-start))
        return end - start
