# -*- encoding: utf-8 -*-
""" Implements methods for RHAI"""

from robottelo.common import conf
from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.vm import VirtualMachine


class AccessInsightsError(Exception):
    """Exception raised for failed Access Insights configuration operations"""


class RHAI(Base):
    def view_registered_systems(self):
        """To view the number of registered systems"""
        result = self.wait_until_element(
            locators['insights.registered_systems']
        ).text
        return result

    def register_client_to_rhai(self, activation_key, org):
        self.vm = VirtualMachine(distro='rhel67')
        self.vm.create()
        # Download and Install ketello-ca rpm
        self.vm.install_katello_cert()
        self.vm.register_contenthost(activation_key, org)

        # Red Hat Access Insights requires RHEL 6/7 repo and it not
        # possible to sync the repo during the tests,
        # adding a file in /etc/yum.repos.d/rhel6/7.repo

        rhel6_repo = conf.properties['insights.rhel6_repo']

        repo_file = (
            '[rhel6-rpms]\n'
            'name=RHEL6\n'
            'baseurl={0}\n'
            'enabled=1\n'
            .format(rhel6_repo)
        )

        self.vm.run(
            'echo "{0}" >> /etc/yum.repos.d/rhel6.repo'
            .format(repo_file)
        )

        # Install redhat-access-insights package
        package_name = 'redhat-access-insights'
        result = self.vm.run('yum install -y {0}'.format(package_name))
        if result.return_code != 0:
            raise AccessInsightsError(
                'Unable to install redhat-access-insights rpm'
            )

        # Verify if package is installed by query it
        result = self.vm.run('rpm -q {0}'.format(package_name))
        if result.return_code != 0:
            raise AccessInsightsError(
                'Unable to install redhat-access-insights rpm'
            )

        # Register client with Red Hat Access Insights
        result = self.vm.run('redhat-access-insights --register')
        if result.return_code != 0:
            raise AccessInsightsError(
                'Unable to register client to Access Insights through '
                'Satellite')
