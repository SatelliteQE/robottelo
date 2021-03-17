"""Tests for http-proxy hammer command.

:Requirement: HttpProxy

:CaseLevel: Acceptance

:CaseComponent: Repositories

:Assignee: tpapaioa

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import pytest
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.http_proxy import HttpProxy


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_update_delete(module_org, module_location):
    """Create new http-proxy with attributes, update and delete it.

    :id: 6045010f-b43b-46f0-b80f-21505fa021c8

    :BZ: 1774325

    :steps:

        1. hammer http-proxy create <args>
        2. hammer http-proxy update <args>
        3. hammer http-proxy delete <args>

    :expectedresults: CRUD operations related to http-proxy hammer command are successful.

    :CaseImportance: Critical
    """
    name = gen_string('alpha', 15)
    url = f'{gen_url(scheme="https")}:{gen_integer(min_value=10, max_value=9999)}'
    password = gen_string('alpha', 15)
    username = gen_string('alpha', 15)

    updated_name = gen_string('alpha', 15)
    updated_url = f'{gen_url(scheme="https")}:{gen_integer(min_value=10, max_value=9999)}'
    updated_password = gen_string('alpha', 15)
    updated_username = gen_string('alpha', 15)

    # Create
    http_proxy = HttpProxy.create(
        {
            'name': name,
            'url': url,
            'username': username,
            'password': password,
            'organization-id': module_org.id,
            'location-id': module_location.id,
        }
    )
    assert http_proxy['name'] == name
    assert http_proxy['url'] == url
    assert http_proxy['username'] == username

    # Update
    HttpProxy.update(
        {
            'name': name,
            'new-name': updated_name,
            'url': updated_url,
            'username': updated_username,
            'password': updated_password,
        }
    )
    updated_http_proxy = HttpProxy.info({'id': http_proxy['id']})
    assert updated_http_proxy['name'] == updated_name
    assert updated_http_proxy['url'] == updated_url
    assert updated_http_proxy['username'] == updated_username

    # Delete
    HttpProxy.delete({'id': updated_http_proxy['id']})
    with pytest.raises(CLIReturnCodeError):
        HttpProxy.info({'id': updated_http_proxy['id']})
