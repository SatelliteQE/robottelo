"""Usage::

    hammer compute_resource [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a compute resource.
    info                          Show an compute resource.
    list                          List all compute resources.
    update                        Update a compute resource.
    delete                        Delete a compute resource.
    image                         View and manage compute resource's images


:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-libvirt

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from fauxfactory import gen_string
from fauxfactory import gen_url

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import make_compute_resource
from robottelo.cli.factory import make_location
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.datafactory import parametrized
from robottelo.decorators import skip_if_not_set


def valid_name_desc_data():
    """Random data for valid name and description"""
    return {
        'numeric': {'name': gen_string('numeric'), 'description': gen_string('numeric')},
        'alpha_long_name': {
            'name': gen_string('alphanumeric', 255),
            'description': gen_string('alphanumeric'),
        },
        'alpha_long_descr': {
            'name': gen_string('alphanumeric'),
            'description': gen_string('alphanumeric', 255),
        },
        'utf8': {'name': gen_string('utf8'), 'description': gen_string('utf8')},
        'html': {
            'name': '<html>{}</html>'.format(gen_string('alpha')),
            'description': '<html>{}</html>'.format(gen_string('alpha')),
        },
        'non_letters': {
            'name': "{0}[]@#$%^&*(),./?\\\"{{}}><|''".format(gen_string('utf8')),
            'description': "{0}[]@#$%^&*(),./?\\\"{{}}><|''".format(gen_string('alpha')),
        },
    }


def invalid_create_data():
    """Random data for invalid name and url"""
    return {
        'long_name': {'name': gen_string('alphanumeric', 256)},
        'empty_name': {'name': ''},
        'invalid_url': {'url': 'invalid url'},
        'empty_url': {'url': ''},
    }


def valid_update_data():
    """Random data for valid update"""
    return {
        'utf8_name': {'new-name': gen_string('utf8', 255)},
        'alpha_name': {'new-name': gen_string('alphanumeric')},
        'white_space_name': {'new-name': 'white spaces %s' % gen_string(str_type='alphanumeric')},
        'utf8_descr': {'description': gen_string('utf8', 255)},
        'alpha_descr': {'description': gen_string('alphanumeric')},
        'gen_url': {'url': gen_url()},
        'local_url': {'url': 'qemu+tcp://localhost:16509/system'},
    }


def invalid_update_data():
    """Random data for invalid update"""
    return {
        'long_name': {'new-name': gen_string('utf8', 256)},
        'empty_name': {'new-name': ''},
        'invalid_url': {'url': 'invalid url'},
        'empty_url': {'url': ''},
    }


@pytest.fixture(scope="module")
@skip_if_not_set('compute_resources')
def libvirt_url():
    return LIBVIRT_RESOURCE_URL % settings.compute_resources.libvirt_hostname


@pytest.mark.tier1
def test_positive_create_with_name(libvirt_url):
    """Create Compute Resource

    :id: 6460bcc7-d7f7-406a-aecb-b3d54d51e697

    :expectedresults: Compute resource is created

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    ComputeResource.create(
        {
            'name': 'cr {}'.format(gen_string(str_type='alpha')),
            'provider': 'Libvirt',
            'url': libvirt_url,
        }
    )


@pytest.mark.tier1
def test_positive_info(libvirt_url):
    """Test Compute Resource Info

    :id: f54af041-4471-4d8e-9429-45d821df0440

    :expectedresults: Compute resource Info is displayed

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    name = gen_string('utf8')
    compute_resource = make_compute_resource(
        {
            'name': name,
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': libvirt_url,
        }
    )
    # factory already runs info, just check the data
    assert compute_resource['name'] == name


@pytest.mark.tier1
def test_positive_list(libvirt_url):
    """Test Compute Resource List

    :id: 11123361-ffbc-4c59-a0df-a4af3408af7a

    :expectedresults: Compute resource List is displayed

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    comp_res = make_compute_resource(
        {'provider': FOREMAN_PROVIDERS['libvirt'], 'url': libvirt_url}
    )
    assert comp_res['name']
    result_list = ComputeResource.list({'search': 'name=%s' % comp_res['name']})
    assert len(result_list) > 0
    result = ComputeResource.exists(search=('name', comp_res['name']))
    assert result


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_by_name(libvirt_url):
    """Test Compute Resource delete

    :id: 7fcc0b66-f1c1-4194-8a4b-7f04b1dd439a

    :expectedresults: Compute resource deleted

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    comp_res = make_compute_resource(
        {'provider': FOREMAN_PROVIDERS['libvirt'], 'url': libvirt_url}
    )
    assert comp_res['name']
    ComputeResource.delete({'name': comp_res['name']})
    result = ComputeResource.exists(search=('name', comp_res['name']))
    assert len(result) == 0


# Positive create
@pytest.mark.tier1
@pytest.mark.upgrade
@pytest.mark.parametrize('options', **parametrized(valid_name_desc_data()))
def test_positive_create_with_libvirt(libvirt_url, options):
    """Test Compute Resource create

    :id: adc6f4f8-6420-4044-89d1-c69e0bfeeab9

    :expectedresults: Compute Resource created

    :CaseImportance: Critical

    :CaseLevel: Component

    :parametrized: yes
    """
    ComputeResource.create(
        {
            'description': options['description'],
            'name': options['name'],
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': gen_url(),
        }
    )


@pytest.mark.tier2
def test_positive_create_with_loc(libvirt_url):
    """Create Compute Resource with location

    :id: 224c7cbc-6bac-4a94-8141-d6249896f5a2

    :expectedresults: Compute resource is created and has location assigned

    :CaseImportance: High

    :CaseLevel: Integration
    """
    location = make_location()
    comp_resource = make_compute_resource({'location-ids': location['id']})
    assert len(comp_resource['locations']) == 1
    assert comp_resource['locations'][0] == location['name']


@pytest.mark.tier2
def test_positive_create_with_locs(libvirt_url):
    """Create Compute Resource with multiple locations

    :id: f665c586-39bf-480a-a0fc-81d9e1eb7c54

    :expectedresults: Compute resource is created and has multiple
        locations assigned

    :CaseImportance: High

    :CaseLevel: Integration
    """
    locations_amount = random.randint(3, 5)
    locations = [make_location() for _ in range(locations_amount)]
    comp_resource = make_compute_resource(
        {'location-ids': [location['id'] for location in locations]}
    )
    assert len(comp_resource['locations']) == locations_amount
    for location in locations:
        assert location['name'] in comp_resource['locations']


# Negative create


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_create_data()))
def test_negative_create_with_name_url(libvirt_url, options):
    """Compute Resource negative create with invalid values

    :id: cd432ff3-b3b9-49cd-9a16-ed00d81679dd

    :expectedresults: Compute resource not created

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    with pytest.raises(CLIReturnCodeError):
        ComputeResource.create(
            {
                'name': options.get('name', gen_string(str_type='alphanumeric')),
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'url': options.get('url', gen_url()),
            }
        )


@pytest.mark.tier2
def test_negative_create_with_same_name(libvirt_url):
    """Compute Resource negative create with the same name

    :id: ddb5c45b-1ea3-46d0-b248-56c0388d2e4b

    :expectedresults: Compute resource not created

    :CaseImportance: High

    :CaseLevel: Component
    """
    comp_res = make_compute_resource()
    with pytest.raises(CLIReturnCodeError):
        ComputeResource.create(
            {
                'name': comp_res['name'],
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'url': gen_url(),
            }
        )


# Update Positive


@pytest.mark.tier1
@pytest.mark.parametrize('options', **parametrized(valid_update_data()))
def test_positive_update_name(libvirt_url, options):
    """Compute Resource positive update

    :id: 213d7f04-4c54-4985-8ca0-d2a1a9e3b305

    :expectedresults: Compute Resource successfully updated

    :CaseImportance: Critical

    :CaseLevel: Component

    :parametrized: yes
    """
    comp_res = make_compute_resource()
    options.update({'name': comp_res['name']})
    # update Compute Resource
    ComputeResource.update(options)
    # check updated values
    result = ComputeResource.info({'id': comp_res['id']})
    assert result['description'] == options.get('description', comp_res['description'])
    assert result['name'] == options.get('new-name', comp_res['name'])
    assert result['url'] == options.get('url', comp_res['url'])
    assert result['provider'].lower() == comp_res['provider'].lower()


# Update Negative


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_update_data()))
def test_negative_update(libvirt_url, options):
    """Compute Resource negative update

    :id: e7aa9b39-dd01-4f65-8e89-ff5a6f4ee0e3

    :expectedresults: Compute Resource not updated

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    comp_res = make_compute_resource()
    with pytest.raises(CLIReturnCodeError):
        ComputeResource.update(dict({'name': comp_res['name']}, **options))
    result = ComputeResource.info({'id': comp_res['id']})
    # check attributes have not changed
    assert result['name'] == comp_res['name']
    options.pop('new-name', None)
    for key in options.keys():
        assert comp_res[key] == result[key]


@pytest.mark.tier2
@pytest.mark.parametrize('set_console_password', ['true', 'false'])
def test_positive_create_with_console_password_and_name(libvirt_url, set_console_password):
    """Create a compute resource with ``--set-console-password``.

    :id: 5b4c838a-0265-4c71-a73d-305fecbe508a

    :expectedresults: No error is returned.

    :BZ: 1100344

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    ComputeResource.create(
        {
            'name': gen_string('utf8'),
            'provider': 'Libvirt',
            'set-console-password': set_console_password,
            'url': gen_url(),
        }
    )


@pytest.mark.tier2
@pytest.mark.parametrize('set_console_password', ['true', 'false'])
def test_positive_update_console_password(libvirt_url, set_console_password):
    """Update a compute resource with ``--set-console-password``.

    :id: ef09351e-dcd3-4b4f-8d3b-995e9e5873b3

    :expectedresults: No error is returned.

    :BZ: 1100344

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    cr_name = gen_string('utf8')
    ComputeResource.create({'name': cr_name, 'provider': 'Libvirt', 'url': gen_url()})
    ComputeResource.update({'name': cr_name, 'set-console-password': set_console_password})
