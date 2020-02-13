"""Tests for http-proxy hammer command.

:Requirement: HttpProxy

:CaseLevel: Acceptance

:CaseComponent: Repositories

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url

from robottelo.cleanup import location_cleanup
from robottelo.cleanup import org_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.http_proxy import HttpProxy
from robottelo.decorators import tier1
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class HttpProxyTestCase(CLITestCase):
    """Tests for http-proxy via Hammer CLI"""

    @tier1
    @upgrade
    def test_positive_create_update_delete(self):
        """Create new http-proxy with attributes, update and delete it.

        :id: 6045010f-b43b-46f0-b80f-21505fa021c8

        :BZ: 1774325

        :steps:

            1. Create http-proxy.
            2. Update http-proxy.
            3. delete http-proxy.

        :expectedresults: CRUD operations related to http-proxy hammer command are successful.

        :CaseImportance: Critical
        """
        loc = make_location()
        org = make_org()
        self.addCleanup(location_cleanup, loc['id'])
        self.addCleanup(org_cleanup, org['id'])
        # Create http proxy
        name = gen_string('alpha', 15)
        url = '{}:{}'.format(
            gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999))
        password = gen_string('alpha', 15)
        username = gen_string('alpha', 15)
        updated_name = gen_string('alpha', 15)
        updated_url = '{}:{}'.format(
            gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999))
        updated_password = gen_string('alpha', 15)
        updated_username = gen_string('alpha', 15)
        http_proxy = HttpProxy.create({
            'name': name,
            'url': url,
            'username': username,
            'password': password,
            'organization-id': org['id'],
            'location-id': loc['id']
        })
        assert http_proxy['name'] == name
        assert http_proxy['url'] == url
        assert http_proxy['username'] == username
        # Update http-proxy
        HttpProxy.update({
            'name': name,
            'new-name': updated_name,
            'url': updated_url,
            'username': updated_username,
            'password': updated_password,
        })
        updated_http_proxy = HttpProxy.info({'id': http_proxy['id']})
        assert updated_http_proxy['name'] == updated_name
        assert updated_http_proxy['url'] == updated_url
        assert updated_http_proxy['username'] == updated_username
        # Delete http-proxy
        HttpProxy.delete({'id': updated_http_proxy['id']})
        with self.assertRaises(CLIReturnCodeError):
            HttpProxy.info({'id': updated_http_proxy['id']})
