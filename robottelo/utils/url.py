from urllib.parse import urlparse

from robottelo.logging import logger


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False


def is_ipv4_url(text):
    # Did not find the better way to filter only URLs so skipping it simple
    # and open for reviewers suggestions
    if isinstance(text, str) and 'ipv4' in text and 'redhat.com' in text:
        return True
    return False


def ipv6_translator(settings_list, setting_major, settings):
    """Translates the hostname containing ipv4 to ipv6 and updates the settings object"""
    dotted_settings = '.'.join(setting_major)
    for _key, _val in settings_list.items():
        if is_ipv4_url(_val):
            settings.set(f'{dotted_settings}.{_key}', str(_val).replace('ipv4', 'ipv6'))
            logger.debug(f'Setting translated to IPv6, Path: {dotted_settings}.{_key}')
        elif isinstance(_val, list):
            updated = False
            new_list = _val
            for i in range(len(new_list)):
                if is_ipv4_url(new_list[i]):
                    new_list[i] = new_list[i].replace('ipv4', 'ipv6')
                    updated = True
            if updated:
                settings.set(f'{dotted_settings}.{_key}', new_list)
                logger.debug(f'Setting translated to IPv6, Path: {dotted_settings}.{_key}')
        elif isinstance(_val, dict):
            new_setting_major = setting_major + [_key]
            ipv6_translator(settings_list=_val, setting_major=new_setting_major, settings=settings)


def ipv6_hostname_translation(settings):
    """Migrates any ipv4 containing hostname in conf to ipv6 hostname"""
    settings_path = []
    if settings.server.is_ipv6:
        all_settings = settings.loaded_by_loaders.items()
        for loader_name, loader_settings in tuple(all_settings):
            if loader_name.loader == 'yaml':
                ipv6_translator(loader_settings, settings_path, settings)
    else:
        logger.debug('Ipv6 Hostname dynaconf migration hook is skipped for ipv4 testing')
