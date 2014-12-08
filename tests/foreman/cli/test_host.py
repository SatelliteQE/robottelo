from fauxfactory import gen_string, gen_integer
from robottelo.test import CLITestCase
from robottelo.cli.factory import (
    CLIFactoryError, make_architecture, make_domain, make_environment,
    make_host, make_location, make_medium, make_org, make_os,
    make_partition_table)
from robottelo.cli.proxy import Proxy


class HostTestCase(CLITestCase):
    """Host CLI tests."""

    def test_positive_create_1(self):
        """@test: A host can be created with a random name

        @feature: Hosts

        @assert: A host is created and the name matches

        """
        # Use the default installation smart proxy
        result = Proxy.list()
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(len(result.stdout), 0)
        puppet_proxy = result.stdout[0]

        host_name = gen_string(str_type='alpha', length=gen_integer(1, 10))

        try:
            # Creating dependent objects
            architecture = make_architecture()
            domain = make_domain()
            environment = make_environment()
            location = make_location()
            medium = make_medium()
            ptable = make_partition_table()
            organization = make_org(cached=True)
            os = make_os({
                u'architecture-ids': architecture['id'],
                u'medium-ids': medium['id'],
                u'ptable-ids': ptable['id'],
            })

            host = make_host({
                u'architecture-id': architecture['id'],
                u'domain-id': domain['id'],
                u'environment-id': environment['id'],
                u'location-id': location['id'],
                u'medium-id': medium['id'],
                u'name': host_name,
                u'operatingsystem-id': os['id'],
                u'organization-id': organization['id'],
                u'partition-table-id': ptable['id'],
                u'puppet-proxy-id': puppet_proxy['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        name = '{0}.{1}'.format(host_name, domain['name']).lower()
        self.assertEqual(host['name'], name)
