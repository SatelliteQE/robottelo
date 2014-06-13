# -*- encoding: utf-8 -*-
"""Utility wrappers for the ``requests`` library."""
from robottelo.common import conf
import json as js
import logging
import requests

logger = logging.getLogger("robottelo")


def request(method, **kwargs):
    """A wrapper around the ``requests.request`` function that provides default
    values for ``domain``, ``auth`` and ``json``, adding new params for each.

    :param method: method for the new :class:`Request` object.
    :param optional url: URL for the new :class:`Request` object.
    :param optional domain: set to main.server.hostname as default
    :param optional path: sets url to "%/%".format(domain,path)
    :param optional params: Dictionary or bytes to be sent
        in the query string for the :class:`Request`.
    :param optional data: Dictionary, bytes, or file-like object to send
        in the body of the :class:`Request`.
    :param optional json: converts python data structure with json.dumps
        and sends it as data, if the data param is empty
    :param optional headers: Dictionary of HTTP Headers to send
    :param optional cookies: Dict or CookieJar object to send
    :param optional files: Dictionary of 'name': file-like-objects
        (or {'name': ('filename', fileobj)}) for multipart encoding upload.
    :param optional auth: Auth tuple to enable Basic/Digest/Custom HTTP Auth.
    :param optional timeout: Float describing the timeout of the request.
    :param optional bool allow_redirects: Set to True if POST/PUT/DELETE
        redirect following is allowed.
    :param optional proxies: Dictionary mapping protocol to the URL of the
        proxy.
    :param optional verify: If ``True``, the SSL cert will be verified. A
        ``CA_BUNDLE`` path can also be provided.
    :param optional stream: If ``False``, the response content will be
        immediately downloaded.
    :param cert: If ``string``, path to SSL client cert file (.pem). If
        ``tuple``, a ``('cert', 'key')`` pair.

    :type cert: tuple or string. Optional.

    """
    if "user" in kwargs:
        user = kwargs.pop("user")
        if user:
            kwargs.setdefault('auth', (
                user.login,
                user.password))

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

    request_command = "request(method={0}, url={1}, **{2}".format(
        method,
        url,
        kwargs)
    logger.debug("Calling %s", request_command)
    res = requests.request(method=method, url=url, **kwargs)
    curl_command = "curl -X {0} {1}  -u {2}:{3} {4} -d {5}".format(
        res.request.method,
        "" if kwargs["verify"] else "-k",
        kwargs["auth"][0],
        kwargs["auth"][1],
        url,
        res.request.body)
    logger.debug(
        str(res.status_code) + " " +
        str(res.content))

    res.__dict__["curl_command"] = curl_command
    res.__dict__["request_command"] = request_command

    return res


def get(**kwargs):
    # pylint: disable=W1401
    """Sends a GET request.

    :param optional \**kwargs: Arguments for ``request``.
    :return: A :class:`Response` object.

    """
    kwargs.setdefault('allow_redirects', True)
    return request('get', **kwargs)


def options(**kwargs):
    # pylint: disable=W1401
    """Sends a OPTIONS request.

    :param optional \**kwargs: Arguments for ``request``.
    :return: A :class:`Response` object.

    """
    kwargs.setdefault('allow_redirects', True)
    return request('options', **kwargs)


def head(**kwargs):
    # pylint: disable=W1401
    """Sends a HEAD request.

    :param optional \**kwargs: Arguments for ``request``.
    :return: A :class:`Response` object.

    """
    kwargs.setdefault('allow_redirects', False)
    return request('head', **kwargs)


def post(json=None, **kwargs):
    # pylint: disable=W1401
    """Sends a POST request.

    :param optional json: Dictionary, bytes, or file-like object to send
    :param optional \**kwargs: Arguments for ``request``.
    :return: A :class:`Response` object.

    """
    return request('post', json=json, **kwargs)


def put(json=None, **kwargs):
    # pylint: disable=W1401
    """Sends a PUT request.

    :param optional data: A dictionary, bytes, or file-like object to send
    :param optional \**kwargs: Arguments for ``request``.
    :return: A :class:`Response` object.

    """
    return request('put', json=json, **kwargs)


def patch(json=None, **kwargs):
    # pylint: disable=W1401
    """Sends a PATCH request.

    :param optional data: A dictionary, bytes, or file-like object to send in
        the body of the :class:`Request`.
    :param optional \**kwargs: Arguments for ``request``.
    :return: A :class:`Response` object.

    """
    return request('patch', json=json, **kwargs)


def delete(**kwargs):
    # pylint: disable=W1401
    """Sends a DELETE request.

    :param optional \**kwargs: Arguments for ``request``.
    :return: A :class:`Response` object.

    """
    return request('delete', **kwargs)
