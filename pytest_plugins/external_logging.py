from robottelo.config import settings


def pytest_addoption(parser):
    """Adds option for enabling external logging"""
    help_text = '''
        Flag for enabling promtail on the spawned hosts.
        This is used for sending of the logs to the external Loki instance

        Usage: --external_logging
    '''
    parser.addoption("--external-logging", action="store_true", default=False, help=help_text)


def pytest_cmdline_main(config):
    if not config.getoption('external_logging', False):
        return
    settings.set('server.deploy_arguments.promtail_enable', True)
    settings.set('capsule.deploy_arguments.promtail_enable', True)
    ch = settings.content_host
    for os in [i for i in ch if isinstance(ch[i], dict) and ch[i].get('vm')]:
        ch[os]['vm']['promtail_enable'] = True
    # update the container env too, if available
    promtail_var = {'PROMTAIL_ENABLE': "True"}
    for os in [i for i in ch if isinstance(ch[i], dict) and ch[i].get('container')]:
        settings.set(f'content_host.{os}.container.environment', promtail_var)
