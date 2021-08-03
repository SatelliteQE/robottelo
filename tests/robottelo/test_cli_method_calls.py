import pytest

from robottelo.cli.org import Org
from robottelo.cli.proxy import Proxy
from robottelo.cli.repository import Repository
from robottelo.cli.subscription import Subscription


@pytest.mark.parametrize(
    'command_sub',
    [
        'add-compute-resource',
        'remove-compute-resource',
        'add-domain',
        'remove-domain',
        'add-environment',
        'remove-environment',
        'add-hostgroup',
        'remove-hostgroup',
        'add-location',
        'remove-location',
        'add-medium',
        'remove-medium',
        'add-provisioning-template',
        'remove-provisioning-template',
        'add-smart-proxy',
        'remove-smart-proxy',
        'add-subnet',
        'remove-subnet',
        'add-user',
        'remove-user',
    ],
)
def test_cli_org_method_called(mocker, command_sub):
    """Check Org methods are called and command_sub edited
    This is a parametrized test called by Pytest for each of Org methods
    """
    execute = mocker.patch('robottelo.cli.org.Org.execute')
    construct = mocker.patch('robottelo.cli.org.Org._construct_command')
    options = {'foo': 'bar'}
    assert execute.return_value == getattr(Org, command_sub.replace('-', '_'))(options)
    assert command_sub == Org.command_sub
    assert construct.called_once_with(options)
    assert execute.called_once_with(construct.return_value)


@pytest.mark.parametrize('command_sub', ['import-classes', 'refresh-features'])
def test_cli_proxy_method_called(mocker, command_sub):
    """Check Proxy methods are called and command_sub edited
    This is a parametrized test called by Pytest for each of Proxy methods
    """
    execute = mocker.patch('robottelo.cli.proxy.Proxy.execute')
    construct = mocker.patch('robottelo.cli.proxy.Proxy._construct_command')
    options = {'foo': 'bar'}
    assert execute.return_value == getattr(Proxy, command_sub.replace('-', '_'))(options)
    assert command_sub == Proxy.command_sub
    assert construct.called_once_with(options)
    assert execute.called_once_with(construct.return_value)


@pytest.mark.parametrize('command_sub', ['synchronize', 'remove-content', 'upload-content'])
def test_cli_repository_method_called(mocker, command_sub):
    """Check Repository methods are called and command_sub edited
    This is a parametrized test called by Pytest for each of Repository methods
    """
    execute = mocker.patch('robottelo.cli.repository.Repository.execute')
    construct = mocker.patch('robottelo.cli.repository.Repository._construct_command')
    options = {'foo': 'bar'}
    assert execute.return_value == getattr(Repository, command_sub.replace('-', '_'))(options)
    assert command_sub == Repository.command_sub
    assert construct.called_once_with(options)
    assert execute.called_once_with(construct.return_value)


@pytest.mark.parametrize('command_sub', ['info', 'create'])
def test_cli_repository_info_and_create(mocker, command_sub):
    """Check Repository info and create are called"""
    execute = mocker.patch(f'robottelo.cli.base.Base.{command_sub}')
    options = {'foo': 'bar'}
    assert execute.return_value == getattr(Repository, command_sub.replace('-', '_'))(options)


@pytest.mark.parametrize(
    'command_sub', ['upload', 'delete-manifest', 'refresh-manifest', 'manifest-history']
)
def test_cli_subscription_method_called(mocker, command_sub):
    """Check Subscription methods are called and command_sub edited
    This is a parametrized test called by Pytest for each
    of Subscription methods
    """
    # avoid BZ call in `upload` method
    execute = mocker.patch('robottelo.cli.subscription.Subscription.execute')
    construct = mocker.patch('robottelo.cli.subscription.Subscription._construct_command')
    options = {'foo': 'bar'}
    assert execute.return_value == getattr(Subscription, command_sub.replace('-', '_'))(options)
    assert command_sub == Subscription.command_sub
    assert construct.called_once_with(options)
    assert execute.called_once_with(construct.return_value)
