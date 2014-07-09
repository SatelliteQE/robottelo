"""Wrappers for methods in the ``requests`` module.

You can read up on Requests here: http://docs.python-requests.org/en/latest/
Details on the wrapped methods are here:
http://docs.python-requests.org/en/latest/api/#main-interface

The various ``_call_requests_*`` functions in this module are extremely simple
wrapper functions. They do not alter the arguments passed to them in any way,
nor do they do anything else such as logging. They exist soley to ease unit
testing: each one can be overridden in a unit test for mocking purposes.

The following methods are also simple wrappers for the corresponding methods in
the ``requests`` module:

* request
* head
* get
* post
* put
* patch
* delete

These methods do not functionally alter the behaviour of their wrapped methods.
However, they do log out information about the request being made before it is
sent, and they log out information about the response received.

"""
from urllib import urlencode
import json as js
import logging
import requests


logger = logging.getLogger(__name__)  # (bad var name) pylint: disable=C0103


def _curl_arg_user(kwargs):
    """Return the curl ``--user <user:password>`` option, if appropriate.

    ``kwargs['auth']`` is used to construct the equivalent curl option, if
    present.

    :param dict kwargs: Keyword arguments, such as one might pass to the
        ``request`` method.
    :return: Either ``'--user <user:password> '`` or ``''``.
    :rtype: str

    """
    if 'auth' in kwargs:
        return '--user {0}:{1} '.format(kwargs['auth'][0], kwargs['auth'][1])
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
        'Making HTTP {0} request to {1} with {2} and {3}.'.format(
            method,
            url,
            'options {0}'.format(kwargs) if len(kwargs) > 0 else 'no options',
            'data {0}'.format(data) if data is not None else 'no data',
        )
    )
# logger.info(
    print 'Equivalent curl command: curl -X {0} {1}{2}{3} {4}'.format(
        method,
        _curl_arg_user(kwargs),
        _curl_arg_insecure(kwargs),
        _curl_arg_data(kwargs),
        url
    )
   # )


def _log_response(response):
    """Log out information about a ``Request`` object.

    After calling ``requests.request`` or one of its convenience methods, the
    object returned can be passed to this method. If done, information about
    the object returned is logged.

    :return: Nothing is returned.
    :rtype: None

    """
    logger.debug('Received HTTP {0} response: {1}'.format(
        response.status_code,
        response.content,
    ))


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
    _log_request(method, url, kwargs)
    response = _call_requests_request(method, url, **kwargs)
    _log_response(response)
    return response


def head(url, **kwargs):
    """A wrapper for ``requests.head``."""
    _log_request('HEAD', url, kwargs)
    response = _call_requests_head(url, **kwargs)
    _log_response(response)
    return response


def get(url, **kwargs):
    """A wrapper for ``requests.get``."""
    _log_request('GET', url, kwargs)
    response = _call_requests_get(url, **kwargs)
    _log_response(response)
    return response


def post(url, data=None, **kwargs):
    """A wrapper for ``requests.post``."""
    print kwargs['json']
    if kwargs.get('json', None):
        try:
            data = js.dumps(kwargs['json'])
        except:
            pass
        finally:
            del kwargs['json']
    print data
    _log_request('POST', url, kwargs, data)
    response = _call_requests_post(url, data, **kwargs)
    _log_response(response)
    return response


def put(url, data=None, **kwargs):
    """A wrapper for ``requests.put``. Sends a PUT request."""
    _log_request('PUT', url, kwargs, data)
    response = _call_requests_put(url, data, **kwargs)
    _log_response(response)
    return response


def patch(url, data=None, **kwargs):
    """A wrapper for ``requests.patch``. Sends a PATCH request."""
    _log_request('PATCH', url, kwargs, data)
    response = _call_requests_patch(url, data, **kwargs)
    _log_response(response)
    return response


def delete(url, **kwargs):
    """A wrapper for ``requests.delete``. Sends a DELETE request."""
    _log_request('DELETE', url, kwargs)
    response = _call_requests_delete(url, **kwargs)
    _log_response(response)
    return response
