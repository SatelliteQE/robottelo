"""Test for Client related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
import time

from fabric.api import execute
from nailgun import entities
from robottelo.test import APITestCase
from robottelo.api.utils import (
    attach_custom_product_subscription,
    call_entity_method_with_timeout
)
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.constants import FAKE_REPO_ZOO3
from upgrade_tests.helpers.scenarios import (
    create_dict,
    dockerize,
    get_entity_data
)


def create_activation_key_for_client_registration(
        ak_name, client_os, org, environment, sat_state):
    """Creates Activation key for client registration

    :param str ak_name: Activation key name
    :param str client_os: rhel6/rhel7
    :param nailgun.entity.Organization org: Organization
    :param nailgun.entity.Environment environment: Environment
    :param str sat_state: pre or post

    :return nailgun.entity.ActivationKey: Activation key
    """
    client_os = client_os.upper()
    from_ver = os.environ.get('FROM_VERSION')
    rhel_prod_name = 'scenarios_rhel{}_prod'.format(client_os[-1])
    rhel_repo_name = '{}_repo'.format(rhel_prod_name)
    rhel_url = os.environ.get('{}_CUSTOM_REPO'.format(client_os))
    if rhel_url is None:
        raise ValueError('The RHEL Repo URL environment variable for OS {} '
                         'is not provided!'.format(client_os))
    rhel_prod = entities.Product(
        name=rhel_prod_name, organization=org.id).create()
    if sat_state.lower() == 'pre' and from_ver in ['6.1', '6.2']:
        rhel_repo = entities.Repository(
            name=rhel_repo_name,
            product=rhel_prod,
            url=rhel_url,
            content_type='yum'
        ).create()
    else:
        rhel_repo = entities.Repository(
            name=rhel_repo_name,
            product=rhel_prod,
            url=rhel_url,
            content_type='yum',
            verify_ssl_on_sync=False
        ).create()
    call_entity_method_with_timeout(rhel_repo.sync, timeout=1400)
    if sat_state.lower() == 'pre':
        product_name = 'Red Hat Enterprise Linux Server'
        repo_name = 'Red Hat Satellite Tools {0} for RHEL ' \
                    '{1} Server RPMs x86_64'.format(from_ver, client_os[-1])
        tools_prod = entities.Product(
            organization=org.id
        ).search(
            query={
                'per_page': 1000,
                'search': 'name="{}"'.format(product_name)
            }
        )[0]
        tools_repo = entities.Repository(
            organization=org.id, product=tools_prod
        ).search(
            query={
                'per_page': 1000,
                'search': 'name="{}"'.format(repo_name)
            }
        )[0]
    elif sat_state.lower() == 'post':
        product_name = 'scenarios_tools_product'
        tools_repo_url = os.environ.get(
            'TOOLS_{}'.format(client_os.upper()))
        if tools_repo_url is None:
            raise ValueError('The Tools Repo URL environment variable for '
                             'OS {} is not provided!'.format(client_os))
        repo_name = '{}_repo'.format(product_name)
        tools_prod = entities.Product(
            organization=org.id
        ).search(query={'search': 'name={}'.format(product_name)})
        if not tools_prod:
            tools_prod = entities.Product(
                name=product_name, organization=org.id).create()
            tools_repo = entities.Repository(
                name=repo_name,
                product=tools_prod,
                url=tools_repo_url,
                content_type='yum'
            ).create()
            tools_repo.sync()
        else:
            tools_repo = entities.Repository(
                organization=org.id, product=tools_prod
            ).search(query={'search': 'name={}'.format(repo_name)})
    tools_cv = entities.ContentView(
        name=ak_name + '_cv',
        label=ak_name + '_cv',
        organization=org.id
    ).create()
    tools_cv.repository = [tools_repo, rhel_repo]
    tools_cv = tools_cv.update(['repository'])
    tools_cv.publish()
    tools_cv = tools_cv.read()  # Published CV with new version
    # Promote CV
    cvv = entities.ContentViewVersion(
        id=max([cvv.id for cvv in tools_cv.version])
    ).read()
    cvv.promote(
        data={
            u'environment_id': environment.id,
            u'force': False
        }
    )
    tools_ak = entities.ActivationKey(
        name=ak_name,
        content_view=tools_cv,
        organization=org.id,
        environment=environment
    ).create()
    if sat_state == 'pre':
        tools_sub = 'Red Hat Satellite Employee Subscription'
        tools_content = 'rhel-{0}-server-satellite-tools-{1}-rpms'.format(
            client_os[-1], from_ver)
    else:
        tools_sub = tools_prod.name
    tools_subscription = entities.Subscription(organization=org.id).search(
        query={
            'search': 'name="{}"'.format(tools_sub),
            'per_page': 1000
        }
    )[0]
    rhel_subscription = entities.Subscription(organization=org.id).search(
        query={
            'search': 'name={}'.format(rhel_prod.name),
            'per_page': 1000
        }
    )[0]
    tools_ak.add_subscriptions(data={
        'subscription_id': tools_subscription.id})
    if sat_state == 'pre':
        tools_ak.content_override(data={
            'content_override':
                {
                    u'content_label': tools_content,
                    u'value': u'1'
                }}
        )
    tools_ak.add_subscriptions(data={
        'subscription_id': rhel_subscription.id})
    return tools_ak


def create_yum_test_repo(product_name, repo_url, org):
    """Creates yum repo from given url and syncs

    :param str product_name: Product name to be created
    :param str repo_url: The repo url for repo
    :param nailgun.entity.Organization org: Organization

    :return tuple(nailgun entities): Returns product and yum_repo
    """
    product = entities.Product(
        name=product_name,
        organization=org,
    ).create()
    yum_repo = entities.Repository(
        name='{}_repo'.format(product_name),
        product=product,
        url=repo_url,
        content_type='yum'
    ).create()
    yum_repo.sync()
    return product, yum_repo


def update_product_subscription_in_ak(product, yum_repo, ak, org):
    """ Updates given products subscription in given AK

    :param nailgun.entity.Product product: products name to calculate
        subscription id
    :param nailgun.entity.Repository yum_repo: yum repository
    :param nailgun.entity.ActivationKey ak: Ak
    :param nailgun.entity.Organization org: Organization
    """
    cv_from_ak = ak.content_view
    cv = cv_from_ak.read()
    cv.repository.append(yum_repo)
    cv = cv.update(['repository'])
    cv.publish()
    cv = cv.read()  # Published CV with new version
    # Promote CV
    environment = entities.ActivationKey(organization=org).search(
        query={'search': 'name={}'.format(ak.name)}
    )[0].environment
    cvv = entities.ContentViewVersion(
        id=max([cvv.id for cvv in cv.version])
    ).read()
    cvv.promote(
        data={
            u'environment_id': environment.id,
            u'force': False
        }
    )
    subscription = entities.Subscription(organization=org).search(query={
        'search': 'name={}'.format(product.name)
    })[0]
    ak.add_subscriptions(data={
        'subscription_id': subscription.id})


class Scenario_upgrade_old_client_and_package_installation(APITestCase):
    """The test class contains pre and post upgrade scenarios to test if the
    package can be installed on preupgrade client remotely

    Test Steps:

        1. Before Satellite upgrade, Create a content host and register it with
            satellite
        2. Upgrade Satellite and Client
        3. Install package post upgrade on a pre-upgrade client from satellite
        4. Check if the package is installed on the pre-upgrade client
    """
    @classmethod
    def setUpClass(cls):
        cls.docker_vm = os.environ.get('DOCKER_VM')
        cls.org = entities.Organization(id=1).read()
        cls.ak_name = 'scenario_old_client_package_install'
        cls.package_name = 'shark'
        cls.prod_name = 'preclient_scenario_product'
        cls.le_lable = cls.le_name = '{}_le'.format(cls.prod_name)

    @pre_upgrade
    def test_pre_scenario_preclient_package_installation(self):
        """Create product and repo from which the package will be installed
        post upgrade

        :id: preupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

        :steps:

            1. Create a content host with existing client ak
            2. Create and sync repo from which the package will be
                installed on content host
            3. Add repo to CV and then in Activation key

        :expectedresults:

            1. The content host is created
            2. The new repo and its product has been added to ak using which
                the content host is created

        """
        prior_env = entities.LifecycleEnvironment(
            organization=self.org
        ).search(query={'search': 'name=Library'})[0]
        environment = entities.LifecycleEnvironment(
            organization=self.org,
            prior=prior_env.id,
            label=self.le_lable,
            name=self.le_name
        ).create()
        ak = create_activation_key_for_client_registration(
            ak_name=self.ak_name,
            client_os='rhel7',
            org=self.org,
            environment=environment,
            sat_state='pre'
        )
        rhel7_client = dockerize(
            ak_name=ak.name, distro='rhel7', org_label=self.org.label)
        client_container_id = list(rhel7_client.values())[0]
        product, yum_repo = create_yum_test_repo(
            product_name=self.prod_name, repo_url=FAKE_REPO_ZOO3, org=self.org)
        update_product_subscription_in_ak(
            product=product, yum_repo=yum_repo, ak=ak, org=self.org)
        attach_custom_product_subscription(
            prod_name=product.name, host_name=str(list(rhel7_client.keys())[0]).lower())
        # Refresh subscriptions on client
        execute(
            docker_execute_command,
            client_container_id,
            'subscription-manager refresh',
            host=self.docker_vm
        )
        # Run goferd on client as its docker container
        kwargs = {'async': True, 'host': self.docker_vm}
        execute(
            docker_execute_command,
            client_container_id,
            'goferd -f',
            **kwargs
        )
        status = execute(docker_execute_command, client_container_id, 'ps -aux',
                         host=self.docker_vm)[self.docker_vm]
        self.assertIn('goferd', status)

        create_dict(
            {self.__class__.__name__: rhel7_client}
        )

    @post_upgrade
    def test_post_scenario_preclient_package_installation(self):
        """Post-upgrade scenario that installs the package on pre-upgrade
        client remotely and then verifies if the package installed

        :id: postupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

        :steps: Install package on a pre-upgrade client

        :expectedresults: The package is installed in client
         """
        client = get_entity_data(self.__class__.__name__)
        client_name = str(list(client.keys())[0]).lower()
        client_id = entities.Host().search(
            query={'search': 'name={}'.format(client_name)}
        )[0].id
        entities.Host().install_content(data={
            'organization_id': self.org.id,
            'included': {'ids': [client_id]},
            'content_type': 'package',
            'content': [self.package_name],
        })
        # Validate if that package is really installed
        installed_package = execute(
            docker_execute_command,
            list(client.values())[0],
            'rpm -q {}'.format(self.package_name),
            host=self.docker_vm
        )[self.docker_vm]
        self.assertIn(self.package_name, installed_package)


class Scenario_upgrade_new_client_and_package_installation(APITestCase):
    """The test class contains post-upgrade scenarios to test if the package
    can be installed on postupgrade client remotely

    Test Steps:

        1. Upgrade Satellite
        2. After Satellite upgrade, Create a content host and register it with
        satellite
        3. Install package a client from satellite
        4. Check if the package is installed on the post-upgrade client
    """
    @classmethod
    def setUpClass(cls):
        cls.docker_vm = os.environ.get('DOCKER_VM')
        cls.org_name = 'new_client_package_install'
        cls.ak_name = 'scenario_new_client_package_install'
        cls.le_name = cls.ak_name+'_env'
        cls.package_name = 'shark'
        cls.prod_name = 'postclient_scenario_product'

    @post_upgrade
    def test_post_scenario_postclient_package_installation(self):
        """Post-upgrade scenario that creates and installs the package on
        post-upgrade client remotely and then verifies if the package installed

        :id: postupgrade-1a881c07-595f-425f-aca9-df2337824a8e

        :steps:

            1. Create a content host with existing client ak
            2. Create and sync repo from which the package will be
                installed on content host
            3. Add repo to CV and then in Activation key
            4. Install package on a pre-upgrade client

        :expectedresults:

            1. The content host is created
            2. The new repo and its product has been added to ak using which
                the content host is created
            3. The package is installed on post-upgrade client
        """
        org = entities.Organization(name=self.org_name).create()
        prior_env = entities.LifecycleEnvironment(organization=org).search(
            query={'search': 'name=Library'}
        )[0]
        environment = entities.LifecycleEnvironment(
            organization=org,
            prior=prior_env.id,
            label=self.le_name,
            name=self.le_name
        ).create()
        ak = create_activation_key_for_client_registration(
            ak_name=self.ak_name,
            client_os='rhel7',
            org=org,
            environment=environment,
            sat_state='post'
        )
        rhel7_client = dockerize(
            ak_name=ak.name, distro='rhel7', org_label=org.label)
        client_container_id = list(rhel7_client.values())[0]
        client_name = list(rhel7_client.keys())[0].lower()
        product, yum_repo = create_yum_test_repo(
            product_name=self.prod_name, repo_url=FAKE_REPO_ZOO3, org=org)
        update_product_subscription_in_ak(
            product=product, yum_repo=yum_repo, ak=ak, org=org)
        attach_custom_product_subscription(
            prod_name=product.name, host_name=client_name)
        # Refresh subscriptions on client
        execute(
            docker_execute_command,
            client_container_id,
            'subscription-manager refresh',
            host=self.docker_vm
        )
        # Run goferd on client as its docker container
        kwargs = {'async': True, 'host': self.docker_vm}
        execute(
            docker_execute_command,
            client_container_id,
            'goferd -f',
            **kwargs
        )
        status = execute(docker_execute_command, client_container_id, 'ps -aux',
                         host=self.docker_vm)[self.docker_vm]
        self.assertIn('goferd', status)
        # Holding on for 30 seconds wihle goferd starts
        time.sleep(30)
        client_id = entities.Host().search(
            query={'search': 'name={}'.format(client_name)}
        )[0].id
        entities.Host().install_content(data={
            'organization_id': org.id,
            'included': {'ids': [client_id]},
            'content_type': 'package',
            'content': [self.package_name],
        })
        # Validate if that package is really installed
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'rpm -q {}'.format(self.package_name),
            host=self.docker_vm
        )[self.docker_vm]
        self.assertIn(self.package_name, installed_package)
