from fauxfactory import gen_string
from nailgun import entities
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo import manifests, ssh
from robottelo.constants import (
    ANY_CONTEXT,
    DEFAULT_SUBSCRIPTION_NAME,
    OSCAP_DEFAULT_CONTENT,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.config import conf
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context, make_hostgroup, make_oscappolicy
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_only_on('sat')
class OpenScap(UITestCase):
    """Implements Product tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        """

        1. Create new organization and environment
        2. Clone and upload manifest
        3. Sync a RedHat repository
        4. Create content-view
        5. Add repository to contet-view
        6. Promote/publish content-view
        7. Create an activation-key
        8. Add product to activation-key
        """
        cls.ak_name = gen_string('alpha')
        org = entities.Organization(name='1kedarb21').create()
        cls.org_name = org.name
        repos = []
        repo_values = [{'repo': REPOS['rhst6']['name'],
                        'reposet': REPOSET['rhst6'],
                        },
                       {'repo': REPOS['rhst7']['name'],
                        'reposet': REPOSET['rhst7'],
                        }
                       ]
        label_values = [{'rhst_label': REPOS['rhst6']['id']},
                        {'rhst_label': REPOS['rhst7']['id']},
                        ]
        # step 1.2: Create new lifecycle environments
        env = entities.LifecycleEnvironment(
            organization=org
        ).create()
        cls.env_name = env.name
        # step 2: Upload manifest
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(org.id, manifest)
        for value in repo_values:
            # step 3.1: Enable RH repo and fetch repository_id
            repository = entities.Repository(id=enable_rhrepo_and_fetchid(
                basearch='x86_64',
                org_id=org.id,
                product=PRDS['rhel'],
                repo=value['repo'],
                reposet=value['reposet'],
                releasever=None,
            ))
            # step 3.2: sync repository
            repository.sync()
            repos.append(repository)
        # step 4: Create content view
        content_view = entities.ContentView(organization=org).create()
        cls.cv_name = content_view.name
        # step 5: Associate repository to new content view
        content_view.repository = repos
        content_view = content_view.update(['repository'])
        # step 6.1: Publish content view
        content_view.publish()
        # step 6.2: Promote content view to lifecycle_env
        content_view = content_view.read()
        # self.assertEqual(len(content_view.version), 1)
        promote(content_view.version[0], env.id)
        # step 7: Create activation key
        activation_key = entities.ActivationKey(
            name=cls.ak_name,
            environment=env,
            organization=org,
            content_view=content_view,
        ).create()
        # step 7.1: Walk through the list of subscriptions.
        # Find the "Red Hat Employee Subscription" and attach it to the
        # recently-created activation key.
        for sub in entities.Subscription(organization=org).search():
            if sub.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                # 'quantity' must be 1, not subscription['quantity']. Greater
                # values produce this error: "RuntimeError: Error: Only pools
                # with multi-entitlement product subscriptions can be added to
                # the activation key with a quantity greater than one."
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': sub.id,
                })
                break
        for value in label_values:
            # step 7.2: Enable product content
            activation_key.content_override(data={'content_override': {
                u'content_label': value['rhst_label'],
                u'value': u'1',
            }})

        super(OpenScap, cls).setUpClass()

    def test_oscap_reports(self):
            """@Test: Perform end to end oscap test.

            @Feature: Oscap End to End.

            @Assert: Oscap reports from rhel6 and rhel7 clients should be
            uploaded to satellite6 and be searchable.

            """
            rhel6_repo = conf.properties['clients.rhel6_repo']
            rhel7_repo = conf.properties['clients.rhel7_repo']
            rhel6_content = OSCAP_DEFAULT_CONTENT['rhel6_content']
            rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
            sat6_hostname = conf.properties['main.server.hostname']
            hgrp6_name = gen_string('alpha')
            hgrp7_name = gen_string('alpha')
            policy_values = [{'content': rhel6_content,
                              'hgrp': hgrp6_name,
                              'policy': gen_string('alpha'),
                              },
                             {'content': rhel7_content,
                              'hgrp': hgrp7_name,
                              'policy': gen_string('alpha'),
                              }]
            vm_values = [{'distro': 'rhel67',
                          'hgrp': hgrp6_name,
                          'rhel_repo': rhel6_repo,
                          },
                         {'distro': 'rhel71',
                          'hgrp': hgrp7_name,
                          'rhel_repo': rhel7_repo,
                          }]
            with Session(self.browser) as session:
                self.puppetclasses.import_scap_client_puppet_classes()
                set_context(session, org=ANY_CONTEXT['org'])
                for content in [rhel6_content, rhel7_content]:
                    session.nav.go_to_oscap_content()
                    self.oscapcontent.update(
                        content,
                        content_org=self.org_name,
                    )
                set_context(session, org=self.org_name)
                for host_group in [hgrp6_name, hgrp7_name]:
                    make_hostgroup(
                        session, name=host_group, content_source=sat6_hostname,
                        puppet_ca=sat6_hostname, puppet_master=sat6_hostname,
                    )
                for value in policy_values:
                    make_oscappolicy(
                        session, name=value['policy'],
                        content=value['content'],
                        profile=OSCAP_PROFILE['rhccp'],
                        period=OSCAP_PERIOD['weekly'],
                        weekday=OSCAP_WEEKDAY['friday'],
                        host_group=value['hgrp'],
                    )
                for value in vm_values:
                    with VirtualMachine(distro=value['distro']) as vm:
                        host = vm.hostname
                        vm.install_katello_cert()
                        vm.register_contenthost(self.ak_name, self.org_name)
                        vm.configure_puppet(value['rhel_repo'])
                        session.nav.go_to_hosts()
                        set_context(session, org=ANY_CONTEXT['org'])
                        self.hosts.update_host_bulkactions(
                            host=host,
                            org=self.org_name
                        )
                        self.hosts.update(
                            name=host,
                            lifecycle_env=self.env_name,
                            cv=self.cv_name,
                            host_group=value['hgrp'],
                            reset_puppetenv=True,
                        )
                        session.nav.go_to_hosts()
                        # Run "puppet agent -t" twice so that it detects it's,
                        # satellite6 and fetch katello SSL certs.
                        for _ in range(2):
                            vm.run(u'puppet agent -t 2> /dev/null')
                        result = vm.run(
                            u'cat /etc/foreman_scap_client/config.yaml'
                            '| grep profile'
                        )
                        self.assertEqual(result.return_code, 0)
                        # BZ 1259188 , required till CH and Hosts unification.
                        # We need to re-register because of above bug and FE
                        vm.register_contenthost(self.ak_name, self.org_name)
                        vm.execute_foreman_scap_client()
                        ssh.command(u'smart-proxy-openscap-send')
                        session.nav.go_to_reports()
                        self.assertTrue(self.oscapreports.search(host))
