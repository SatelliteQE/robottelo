"""Wrappers for methods in the `Requests`_ module.

The functions in this module wrap `functions from`_ the `Requests`_ module.
Each function is modified with the following behaviours:

1. It sets its 'content-type' of 'application/json', so long as no content-type
   is already set.
2. It encodes its ``data`` argument as JSON (using the ``json`` module) if its
   'content-type' is 'application/json'.
3. It logs out information about the request before it is sent.
4. It logs out information about the response when it is received.

The various ``_call_requests_*`` functions in this module are extremely simple
wrapper functions. They sit in the call chain between this module's public
wrappers and the `Requests`_ functions being wrapped. For example,
``_call_requests_post`` is called by :func:`post`, and it calls
``requests.post``. The ``_call_requests_*`` functions do not alter the
arguments passed to them in any way, nor do they do anything else such as
logging. They exist soley to ease unit testing: each one can be overridden in a
unit test for mocking purposes.

.. _Requests: http://docs.python-requests.org/en/latest/
.. _functions from:
    http://docs.python-requests.org/en/latest/api/#main-interface

"""
from urllib import urlencode
import json
import logging
import requests


logger = logging.getLogger(__name__)  # (bad var name) pylint: disable=C0103


def _content_type_is_json(kwargs):
    """Check whether the content-type in ``kwargs`` is 'application/json'.

    :param dict kwargs: The keyword args supplied to :func:`request` or one of
        the convenience functions like it.
    :returns: ``True`` or ``False``
    :rtype: bool

    """
    if 'headers' in kwargs and 'content-type' in kwargs['headers']:
        return kwargs['headers']['content-type'].lower() == 'application/json'
    else:
        return False


def _set_content_type(kwargs):
    """If the 'content-type' header is unset, set it to 'applcation/json'.

    The 'content-type' will not be set if doing a file upload as requests will
    automatically set it.

    :param dict kwargs: The keyword args supplied to :func:`request` or one of
        the convenience functions like it.
    :return: Nothing. ``kwargs`` is modified in-place.

    """
    if 'files' in kwargs:
        return  # requests will automatically set content-type

    headers = kwargs.pop('headers', {})
    headers.setdefault('content-type', 'application/json')
    kwargs['headers'] = headers


def _curl_arg_user(kwargs):
    """Return the curl ``--user <user:password>`` option, if appropriate.

    ``kwargs['auth']`` is used to construct the equivalent curl option, if
    present.

    :param dict kwargs: Keyword arguments, such as one might pass to the
        ``request`` method.
    :return: Either ``'--user <user:password> '`` or ``''``.
    :rtype: str

    """
    # True if user provided creds in this form: auth=('username', 'password')
    # False if no creds or in e.g. this form: auth=HTTPBasicAuth('usr', 'pass')
    if 'auth' in kwargs and isinstance(kwargs['auth'], tuple):
        return u'--user {0}:{1} '.format(kwargs['auth'][0], kwargs['auth'][1])
    return ''


def _curl_arg_insecure(kwargs):
    """Return the curl ``--insecure`` option, if appropriate.

    Return the curl option for disabling SSL verification if ``kwargs``
    contains an equivalent option. Return no curl option otherwise.

    :param dict kwargs: Keyword arguments, such as one might pass to the
        ``request`` method.
    :return: Either ``'--insecure '`` or ``''``.
    :rtype: str

    """
    if 'verify' in kwargs and kwargs['verify'] is False:
        return '--insecure '
    return ''


def _curl_arg_data(kwargs):
    """Return the curl ``--data <data>`` option.

    Return the curl ``--data <data>`` option, and use ``kwargs`` as ``<data>``.
    Ignore the ``'auth'`` and ``'verify'`` keys when assembling ``<data>``.

    :param dict kwargs: Keyword arguments, such as one might pass to the
        ``request`` method.
    :return: The curl ``--data <data>`` option.
    :rtype: str

    """
    trimmed_kwargs = kwargs.copy()
    for key in ('auth', 'verify'):
        trimmed_kwargs.pop(key, None)
    return urlencode(trimmed_kwargs)


def _log_request(method, url, kwargs, data=None):
    """Log out information about the arguments given.

    The arguments provided to this function correspond to the arguments that
    one can pass to ``requests.request``.

    :return: Nothing is returned.
    :rtype: None

    """
    logger.info(
        'Making HTTP %s request to %s with %s and %s.',
        method,
        url,
        'options {0}'.format(kwargs) if len(kwargs) > 0 else 'no options',
        'data {0}'.format(data) if data is not None else 'no data',
    )
    logger.info(
        'Equivalent curl command: curl -X %s %s%s%s %s',
        method,
        _curl_arg_user(kwargs),
        _curl_arg_insecure(kwargs),
        _curl_arg_data(kwargs),
        url,
    )


def _log_response(response):
    """Log out information about a ``Request`` object.

    After calling ``requests.request`` or one of its convenience methods, the
    object returned can be passed to this method. If done, information about
    the object returned is logged.

    :return: Nothing is returned.
    :rtype: None

    """
    logger.debug(
        'Received HTTP %s response: %s',
        response.status_code,
        response.content,
    )


def _call_requests_request(method, url, **kwargs):
    """Call ``requests.request``."""
    return requests.request(method, url, **kwargs)


def _call_requests_head(url, **kwargs):
    """Call ``requests.head``."""
    return requests.head(url, **kwargs)


def _call_requests_get(url, **kwargs):
    """Call ``requests.get``."""
    return requests.get(url, **kwargs)


def _call_requests_post(url, data=None, **kwargs):
    """Call ``requests.post``."""
    return requests.post(url, data, **kwargs)


def _call_requests_put(url, data=None, **kwargs):
    """Call ``requests.put``."""
    return requests.put(url, data, **kwargs)


def _call_requests_patch(url, data=None, **kwargs):
    """Call ``requests.patch``."""
    return requests.patch(url, data, **kwargs)


def _call_requests_delete(url, **kwargs):
    """Call ``requests.delete``."""
    return requests.delete(url, **kwargs)


def request(method, url, **kwargs):
    """A wrapper for ``requests.request``."""
    _set_content_type(kwargs)
    if _content_type_is_json(kwargs) and kwargs.get('data') is not None:
        kwargs['data'] = json.dumps(kwargs['data'])
    _log_request(method, url, kwargs)
    response = _call_requests_request(method, url, **kwargs)
    _log_response(response)
    return response


def head(url, **kwargs):
    """A wrapper for ``requests.head``."""
    _set_content_type(kwargs)
    if _content_type_is_json(kwargs) and kwargs.get('data') is not None:
        kwargs['data'] = json.dumps(kwargs['data'])
    _log_request('HEAD', url, kwargs)
    response = _call_requests_head(url, **kwargs)
    _log_response(response)
    return response


def get(url, **kwargs):
    """A wrapper for ``requests.get``."""
    _set_content_type(kwargs)
    if _content_type_is_json(kwargs) and kwargs.get('data') is not None:
        kwargs['data'] = json.dumps(kwargs['data'])
    _log_request('GET', url, kwargs)
    response = _call_requests_get(url, **kwargs)
    _log_response(response)
    return response


def post(url, data=None, **kwargs):
    """A wrapper for ``requests.post``."""
    _set_content_type(kwargs)
    if _content_type_is_json(kwargs) and data is not None:
        data = json.dumps(data)
    _log_request('POST', url, kwargs, data)
    response = _call_requests_post(url, data, **kwargs)
    _log_response(response)
    return response


def put(url, data=None, **kwargs):
    """A wrapper for ``requests.put``. Sends a PUT request."""
    _set_content_type(kwargs)
    if _content_type_is_json(kwargs) and data is not None:
        data = json.dumps(data)
    _log_request('PUT', url, kwargs, data)
    response = _call_requests_put(url, data, **kwargs)
    _log_response(response)
    return response


def patch(url, data=None, **kwargs):
    """A wrapper for ``requests.patch``. Sends a PATCH request."""
    _set_content_type(kwargs)
    if _content_type_is_json(kwargs) and data is not None:
        data = json.dumps(data)
    _log_request('PATCH', url, kwargs, data)
    response = _call_requests_patch(url, data, **kwargs)
    _log_response(response)
    return response


def delete(url, **kwargs):
    """A wrapper for ``requests.delete``. Sends a DELETE request."""
    _set_content_type(kwargs)
    if _content_type_is_json(kwargs) and kwargs.get('data') is not None:
        kwargs['data'] = json.dumps(kwargs['data'])
    _log_request('DELETE', url, kwargs)
    response = _call_requests_delete(url, **kwargs)
    _log_response(response)
    return response
