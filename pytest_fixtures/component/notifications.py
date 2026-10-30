"""SMTP delivery fixtures for notifications on foremanctl hosts."""

from contextlib import ExitStack
from shlex import quote

from fauxfactory import gen_string
import pytest
from wait_for import wait_for


def _execute_checked(target_sat, command):
    result = target_sat.execute(command)
    assert result.status == 0, f'Command failed: {command}: {result.stderr}'
    return result


def _restore_setting(setting, value):
    setting.value = value
    setting.update(['value'])


def _change_setting(target_sat, cleanup, name, value):
    setting = target_sat.api.Setting().search(query={'search': f'name={name}'})[0]
    cleanup.callback(_restore_setting, setting, setting.value)
    setting.value = value
    setting.update(['value'])


def _mailpit_command(mailpit, path):
    return (
        'podman exec foreman curl --noproxy "*" --fail --silent --show-error --max-time 10 '
        f'{quote(f"http://{mailpit}:8025{path}")}'
    )


@pytest.fixture(scope='module')
def use_smtp_mail_delivery(module_target_sat):
    """Share Mailpit for a module and restore SMTP settings when the module finishes."""
    lock_dir = '/run/robottelo-notifications.lock'
    wait_for(
        func=module_target_sat.execute,
        func_args=[f'mkdir -m 0700 {lock_dir}'],
        fail_condition=lambda res: res.status != 0,
        timeout=1800,
        delay=5,
    )
    with ExitStack() as cleanup:
        cleanup.callback(_execute_checked, module_target_sat, f'rmdir {lock_dir}')
        networks = _execute_checked(
            module_target_sat,
            "podman inspect foreman --format "
            "'{{range $name, $network := .NetworkSettings.Networks}}{{$name}} {{end}}'",
        ).stdout.split()
        assert networks, 'Foreman must be attached to a Podman network'
        mailpit = f'robottelo-mailpit-{gen_string("alpha").lower()}'
        cleanup.callback(
            _execute_checked, module_target_sat, f'podman rm -f --ignore {quote(mailpit)}'
        )
        network_args = ' '.join(f'--network {quote(network)}' for network in networks)
        _execute_checked(
            module_target_sat,
            f'podman run -d --name {quote(mailpit)} {network_args} '
            'docker.io/axllent/mailpit:v1.27.4 '
            '--smtp :1025 --listen :8025 --smtp-disable-rdns --disable-version-check --max 0',
        )
        wait_for(
            func=module_target_sat.execute,
            func_args=[_mailpit_command(mailpit, '/readyz')],
            fail_condition=lambda res: res.status != 0,
            timeout=60,
            delay=1,
        )
        workers = _execute_checked(
            module_target_sat, "podman ps --filter name=^dynflow-sidekiq- --format '{{.Names}}'"
        ).stdout.split()
        probe = 'Timeout.timeout(5) { Net::SMTP.start(ARGV[0], 1025) {} }'
        for container in ['foreman', *workers]:
            _execute_checked(
                module_target_sat,
                f'podman exec {quote(container)} ruby -rnet/smtp -rtimeout '
                f'-e {quote(probe)} {quote(mailpit)}',
            )
        for name, value in (
            ('smtp_authentication', ''),
            ('smtp_user_name', ''),
            ('smtp_enable_starttls_auto', False),
            ('smtp_address', mailpit),
            ('smtp_port', 1025),
        ):
            _change_setting(module_target_sat, cleanup, name, value)
        yield {'mailpit': mailpit}


@pytest.fixture
def notification_mail(use_smtp_mail_delivery):
    """Give each test its own recipient in the module's shared Mailpit container."""
    return {
        **use_smtp_mail_delivery,
        'address': f'root+{gen_string("alphanumeric")}@localhost',
    }
