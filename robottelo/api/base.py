# -*- encoding: utf-8 -*-

"""
Module containing utility wrappers
around requests library
"""

import json as js
import requests

from robottelo.common import conf


def request(method, **kwargs):
    """Wrapper around requests.request function, that adds default domain,
    auth and json body, adding new params for each of them.

    :param method: method for the new :class:`Request` object.
    :param url (optional): URL for the new :class:`Request` object.
    :param domain: (optional) set to main.server.hostname as default
    :param path: (optional)   sets url to "%/%".format(domain,path)
    :param params: (optional) Dictionary or bytes to be sent
        in the query string for the :class:`Request`.
    :param data: (optional) Dictionary, bytes, or file-like object to send
        in the body of the :class:`Request`.
    :param json: (optional) converts python data structure with json.dumps
        and sends it as data, if the data param is empty
    :param headers: (optional) Dictionary of HTTP Headers to send
    :param cookies: (optional) Dict or CookieJar object to send
    :param files: (optional) Dictionary of 'name': file-like-objects
        (or {'name': ('filename', fileobj)}) for multipart encoding upload.
    :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
    :param timeout: (optional) Float describing the timeout of the request.
    :param allow_redirects: (optional) Boolean.
        Set to True if POST/PUT/DELETE redirect following is allowed.
    :param proxies: (optional) Dictionary mapping protocol to the URL
        of the proxy.
    :param verify: (optional) if ``True``, the SSL cert will be verified.
        A CA_BUNDLE path can also be provided.
    :param stream: (optional) if ``False``,
        the response content will be immediately downloaded.
    :param cert: (optional) if String, path to ssl client cert file (.pem).
        If Tuple, ('cert', 'key') pair.
"""

    kwargs.setdefault('verify', False)
    kwargs.setdefault('domain', conf.properties['main.server.hostname'])
    kwargs.setdefault('schema', "https://")
    kwargs.setdefault('auth', (
        conf.properties['foreman.admin.username'],
        conf.properties['foreman.admin.password']))
    kwargs.setdefault('headers', {'Content-type': 'application/json'})

    if kwargs.get('path', None):
        url = "{0}{1}{2}".format(
            kwargs['schema'],
            kwargs['domain'],
            kwargs['path'])
        del kwargs['path']
    else:
        url = kwargs['url']
        del kwargs['url']

    if kwargs.get('json', None):
        try:
            kwargs.setdefault('data', js.dumps(kwargs['json']))
        except:
            pass
        finally:
            del kwargs['json']

    del kwargs['domain']
    del kwargs['schema']

    return requests.request(method=method, url=url, **kwargs)


def get(**kwargs):
    """Sends a GET request. Returns :class:`Response` object.

    :param \*\*kwargs: Optional arguments that ``request`` takes.
    """

    kwargs.setdefault('allow_redirects', True)
    return request('get', **kwargs)


def options(**kwargs):
    """Sends a OPTIONS request. Returns :class:`Response` object.

    :param \*\*kwargs: Optional arguments that ``request`` takes.
    """

    kwargs.setdefault('allow_redirects', True)
    return request('options', **kwargs)


def head(**kwargs):
    """Sends a HEAD request. Returns :class:`Response` object.

    :param \*\*kwargs: Optional arguments that ``request`` takes.
    """

    kwargs.setdefault('allow_redirects', False)
    return request('head', **kwargs)


def post(json=None, **kwargs):
    """Sends a POST request. Returns :class:`Response` object.

    :param json: (optional) Dictionary, bytes, or file-like object to send
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('post', json=json, **kwargs)


def put(json=None, **kwargs):
    """Sends a PUT request. Returns :class:`Response` object.

    :param data: (optional) Dictionary, bytes, or file-like object to send
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('put', json=json, **kwargs)


def patch(json=None, **kwargs):
    """Sends a PATCH request. Returns :class:`Response` object.

    :param data: (optional) Dictionary, bytes, or file-like object
        to send in the body of the :class:`Request`.
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('patch', json=json, **kwargs)


def delete(**kwargs):
    """Sends a DELETE request. Returns :class:`Response` object.

    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('delete', **kwargs)
