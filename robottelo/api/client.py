"""Wrappers for methods in the ``requests`` module.

You can read up on Requests here: http://docs.python-requests.org/en/latest/
Details on the wrapped methods are here:
http://docs.python-requests.org/en/latest/api/#main-interface

"""
from urllib import urlencode
import logging
import requests


logger = logging.getLogger(__name__)  # (bad var name) pylint: disable=C0103


def _curl_arg_user(kwargs):
    """Return the curl ``--user <user:password>`` option, if appropriate.

    ``kwargs['auth']`` is used to construct the equivalent curl option, if
    present.

    :param dict kwargs: Arguments, such as one might pass to the ``request``
        method.
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

    :param dict kwargs: Arguments, such as one might pass to the ``request``
        method.
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

    :param dict kwargs: Arguments, such as one might pass to the ``request``
        method.
    :return: The curl ``--data <data>`` option.
    :rtype: str

    """
    trimmed_kwargs = kwargs
    for key in ('auth', 'verify'):
        trimmed_kwargs.pop(key, None)
    return urlencode(trimmed_kwargs)


def _call_requests_request(method, url, **kwargs):
    """Call ``requests.request``. Pass all arguments to that function.

    This function is a stupid-simple wrapper around the ``requests.request``
    function. It does not alter the behaviour of that function in any way. This
    function exists soley to make unit testing easier: this function can be
    overridden to mock ``requests.request``.

    """
    return requests.request(method, url, **kwargs)


def request(method, url, **kwargs):
    """A wrapper for ``requests.request``.

    This wrapper does not change the functional behaviour of
    ``requests.request``. Instead, it logs out information about the the
    request and response.

    For detailed information about the behaviour and arguments of
    ``requests,request``, see:
    http://docs.python-requests.org/en/latest/api/#requests.request.

    :param str method: method for the new Request object.
    :param str url: URL for the new Request object.
    :param \**kwargs: Other, optional arguments for the new Request object.
    :return: A ``Response`` object.
    :rtype: Response

    """
    # provide info about call
    logger.info(
        'Making HTTP {0} request to {1} with the following options: '
        '{2}'.format(method, url, kwargs)
    )
    logger.info('Equivalent curl command: curl -X {0} {1}{2}{3} {4}'.format(
        method,
        _curl_arg_user(kwargs),
        _curl_arg_insecure(kwargs),
        _curl_arg_data(kwargs),
        url
    ))

    # provide info about response
    response = _call_requests_request(method, url, **kwargs)
    logger.debug('Received HTTP {0} response: {1}'.format(
        response.status_code,
        response.content,
    ))
    return response
