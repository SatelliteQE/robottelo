"""Shared function is a decorator, that enable a function once called to store
the results to storage, any ulterior call from the same or other processes will
return the stored results, which make the shared function results persistent.

Note: Shared function store it's data as json. The results of the decorated
    function must be json compatible.

Usage::


    from robottelo.utils.decorators.func_shared.shared import shared

    @shared
    def module_level_shared(*args, **kwargs):
        # do some
        # the result of a shared function must be json compatible
        return any_data

    class SomeTestCase1(TestCase):

        @shared
        def _shared_function(cls):

            org = make_org()
            # upload manifest
            repo = make_repository()
            return dict(org=org, repo=repo}

        @classmethod
        @shared
        def setUpClass(cls):

            data = cls._shared_function()
            other_data = module_level_shared()

            cls.org = data['org']
            cls.repo = data['repo']
            return

    # the shared function can be called an other time to be able to initiate
    # specific data

    class SomeTestCase2(TestCase):

        @classmethod
        @shared(inject=True, injected_kw='_injected')
        def setUpClass(cls, org=None, repo=None, _injected=False):

            if _injected:
                cls.org = org
                cls.repo = repo
            else:
                # create the org
                cls.org = make_org()
                # upload manifest
                cls.repo = make_repository()

            # create a virtual machine

            # shared function with injected=True, must return a dict
            # the resulting dictionary will be injected in other calls as
            # kwargs, an added bool kw argument by default named _injected
            # should be added to the function kwargs, to be able to be notified
            # that the kwargs are injected from already stored result
            return dict(org=cls.org, repo=cls.repo}

        # in case we do not want the injected key word in kwargs
        # simply , declare injected_kw=None
        @classmethod
        @shared(inject=True, injected_kw=None)
        def shared_class_method(cls, org=None, repo=None):
             if org is not None:
                cls.org = org
             else:
                # create the org
                cls.org = make_org()
                # upload manifest
             if repo_id is not None:
                cls.repo = repo
             else:
                cls.repo = make_repository()

            # create a virtual machine

            return dict(org=cls.org, repo=cls.repo}
"""
import datetime
import functools
import hashlib
import inspect
import os
import sys
import traceback
import uuid
from importlib import import_module

from nailgun.entities import Entity

from robottelo.config import setting_is_set
from robottelo.config import settings
from robottelo.logging import logger
from robottelo.utils.decorators.func_shared import file_storage
from robottelo.utils.decorators.func_shared import redis_storage
from robottelo.utils.decorators.func_shared.file_storage import FileStorageHandler
from robottelo.utils.decorators.func_shared.redis_storage import RedisStorageHandler


_storage_handlers = {'file': FileStorageHandler, 'redis': RedisStorageHandler}

DEFAULT_STORAGE_HANDLER = 'file'
# by default using the shared data is disabled
ENABLED = False
NAMESPACE_SCOPE = None
# after 24 hours the shared function data will became not valid
SHARE_DEFAULT_TIMEOUT = 86400
DEFAULT_CALL_RETRIES = 2

_configured = False

_NAMESPACE_SCOPE_KEY_TYPE = 'shared_function'
_DEFAULT_CLASS_NAME_DEPTH = 3

_STATE_READY = 'READY'
_STATE_FAILED = 'FAILED'

_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

_SERVER_CERT_MD5 = None


def _set_configured(value):
    global _configured
    _configured = bool(value)


def _check_config():
    global _configured
    global DEFAULT_STORAGE_HANDLER
    global ENABLED
    global NAMESPACE_SCOPE
    global SHARE_DEFAULT_TIMEOUT
    global DEFAULT_CALL_RETRIES
    if not _configured and setting_is_set('shared_function'):
        DEFAULT_STORAGE_HANDLER = settings.shared_function.storage
        ENABLED = settings.shared_function.enabled
        NAMESPACE_SCOPE = settings.shared_function.scope
        SHARE_DEFAULT_TIMEOUT = settings.shared_function.share_timeout
        DEFAULT_CALL_RETRIES = settings.shared_function.call_retries
        file_storage.LOCK_TIMEOUT = settings.shared_function.lock_timeout
        redis_storage.LOCK_TIMEOUT = settings.shared_function.lock_timeout
        redis_storage.REDIS_HOST = settings.shared_function.redis_host
        redis_storage.REDIS_PORT = settings.shared_function.redis_port
        redis_storage.REDIS_DB = settings.shared_function.redis_db
        redis_storage.REDIS_PASSWORD = settings.shared_function.redis_password
        _set_configured(True)


def enable_shared_function(value):
    """force and override settings, by setting the global use shared data
    attribute
    """
    global ENABLED
    ENABLED = bool(value)


def set_default_scope(value):
    """Set the default namespace scope
    :type value: str or callable
    """
    global NAMESPACE_SCOPE
    NAMESPACE_SCOPE = value


def _get_default_scope():
    """Return the shared function default scope"""

    _check_config()

    if NAMESPACE_SCOPE:
        return NAMESPACE_SCOPE

    return str(format(os.getppid()))


def _get_default_storage_handler():
    """Return the storage handler instance"""
    if DEFAULT_STORAGE_HANDLER not in _storage_handlers:
        raise SharedFunctionError(f'storage handler: "{DEFAULT_STORAGE_HANDLER}" not supported')
    return _storage_handlers.get(DEFAULT_STORAGE_HANDLER)()


class SharedFunctionError(Exception):
    """Shared function related exception"""


class SharedFunctionException(Exception):
    """Shared function call exception when not able to restore the original
    exception
    """


class _SharedFunction:
    """Internal class helper that is created each time the shared function is
    launched and group all the necessary functionality
    """

    def __init__(
        self,
        function_key,
        function,
        args=None,
        kwargs=None,
        retries=DEFAULT_CALL_RETRIES,
        storage_handler=None,
        timeout=SHARE_DEFAULT_TIMEOUT,
        inject=False,
        injected_kw='_inject',
    ):

        if storage_handler is None:
            storage_handler = _get_default_storage_handler()

        if storage_handler is None:
            raise SharedFunctionError('storage_handler not supplied')
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        self._function = function
        self._function_args = args
        self._function_kwargs = kwargs
        self._function_key = function_key
        self._storage_handler = storage_handler
        self._inject = inject
        self._injected_kw = injected_kw
        if not retries:
            retries = 1
        self._max_retries = retries
        self._transaction = uuid.uuid4().hex
        self._share_timeout = timeout

    @property
    def storage(self):
        return self._storage_handler

    @property
    def key(self):
        return self._function_key

    @property
    def transaction(self):
        return self._transaction

    def _encode_result_kwargs(self, kwargs):
        """look for some special kwargs and convert them"""
        if kwargs and isinstance(kwargs, dict):
            for key, value in kwargs.items():
                if isinstance(value, Entity):
                    kwargs[key] = value.to_json_dict()

        return kwargs

    def _call_function(self):

        retries = self._max_retries
        if not retries:
            retries = 1

        exp = None
        result = None
        traceback_text = None
        for retry_index in range(retries):
            exp = None
            traceback_text = None
            try:
                logger.info(
                    'calling shared function: {} - retry index: {}'.format(
                        self._function_key, retry_index
                    )
                )
                result = self._function(*self._function_args, **self._function_kwargs)
                break
            except Exception as err:
                exp = err
                result = None
                logger.exception(exp)
                _, _, traceback_ = sys.exc_info()
                traceback_text = ''.join(traceback.format_tb(traceback_))

        return result, exp, traceback_text

    def _has_result_expired(self, creation_datetime):
        expire_datetime = creation_datetime + datetime.timedelta(seconds=self._share_timeout)

        if datetime.datetime.utcnow() >= expire_datetime:
            return True

        return False

    def __call__(self):
        # this lock prevent any other process to run the function,
        # and if an other process is running the function, I should wait it
        # to finish
        # note: when results are ready this lock has a very short time
        with self.storage.lock(self.key) as data:
            self.storage.when_lock_acquired(data)
            # first must investigate, call the function or use the results
            result = None
            error = None
            traceback_text = ''
            error_class_name = None
            exp = None
            pid = None
            value = self.storage.get(self.key)
            if value is None:
                call_function = True
            else:
                state = value['state']
                result = value['result']
                error = value['error']
                traceback_text = value.get('traceback', '')
                error_class_name = value.get('error_class_name')
                pid = value['pid']
                creation_datetime = datetime.datetime.strptime(
                    value['creation_datetime'], _DATETIME_FORMAT
                )

                if state in [_STATE_READY, _STATE_FAILED] and not self._has_result_expired(
                    creation_datetime
                ):
                    call_function = False
                else:
                    call_function = True

            if call_function is True:
                result, exp, traceback_text = self._call_function()
                creation_datetime = datetime.datetime.utcnow().strftime(_DATETIME_FORMAT)
                if exp:
                    error = str(exp) or 'error occurred'
                    error_class_name = '{}.{}'.format(
                        exp.__class__.__module__, exp.__class__.__name__
                    )
                    value = dict(
                        state=_STATE_FAILED,
                        id=self.transaction,
                        result=None,
                        error=error,
                        error_class_name=error_class_name,
                        traceback=traceback_text,
                        pid=os.getpid(),
                        creation_datetime=creation_datetime,
                    )
                else:
                    error = None
                    result = self._encode_result_kwargs(result)
                    value = dict(
                        state=_STATE_READY,
                        id=self.transaction,
                        result=result,
                        error=error,
                        pid=os.getpid(),
                        creation_datetime=creation_datetime,
                    )
                self.storage.set(self.key, value)

        if call_function and exp:
            # i'am in the first launched process
            raise exp

        if not call_function and error:
            # I am getting my data from storage
            # try to restore the original exception
            logger.error(f'restoring stored exception from PID: {pid}')
            if traceback_text:
                sys.stderr.write(traceback_text)

            if error_class_name:
                # replace the last point with :
                exp_list = error_class_name.split('.')
                exp_list_last = exp_list.pop()
                module_name = '.'.join(exp_list)
                error_class_name = ':'.join([module_name, exp_list_last])
                exp_class = getattr(import_module(module_name), exp_list_last)
                try:
                    exp = exp_class(error)
                except Exception as err:
                    exp = None
                    logger.error(f'was not able to restore exception class {error_class_name}')
                    # log only a simple error, to not be confused with this
                    # exception
                    logger.error(str(err))

                if exp:
                    raise exp

            # if was not able to restore the original exception raise this one
            raise SharedFunctionException(
                'Error generated by process: {} Exception: {}'
                ' error: {}'.format(pid, error_class_name, error)
            )

        if not call_function and self._inject:
            # note: to be able to use this functionality the result must be a
            # dict
            if self._injected_kw:
                # update the kwargs with a kw to notify the function that the
                # kwargs are injected from saved data
                result[self._injected_kw] = True
            # recall the function with result as kwargs
            # the function may modify the result
            result = self._function(*self._function_args, **result)

        return result


def _get_kwargs_md5(**kwargs):
    """Create an md5 hexdigest from kwargs"""
    hd = None
    if kwargs:
        text = f'{tuple(sorted(kwargs.items()))}'
        md = hashlib.md5(text.encode())
        hd = md.hexdigest()
    return hd


def _get_scope_name(scope=None, scope_kwargs=None, scope_context=None):
    if scope_kwargs is None:
        scope_kwargs = {}

    if not scope:
        # from config we receive an empty string for the scope
        scope = _get_default_scope

    scope_names = []

    scope_name = ''
    if scope and callable(scope):
        scope_name = scope(**scope_kwargs)

    if scope_name:
        scope_names.append(scope_name)

    scope_names.append(_NAMESPACE_SCOPE_KEY_TYPE)

    if scope_context:
        scope_names.append(scope_context)

    if scope_names:
        scope_name = '.'.join(scope_names)

    return scope_name


def _get_function_name(function, class_name=None, kwargs=None):
    """Return a string representation of the function as
    module_path.Class_name.function_name

    note: the class name is the first parent class
    """
    if kwargs is None:
        kwargs = {}
    names = [function.__module__]
    if class_name:
        names.append(class_name)
    names.append(function.__name__)
    kwargs_md5 = _get_kwargs_md5(**kwargs)
    if kwargs_md5:
        names.append(kwargs_md5)
    return '.'.join(names)


def _get_function_name_key(function_name, scope=None, scope_kwargs=None, scope_context=None):
    scope_name = _get_scope_name(
        scope=scope, scope_kwargs=scope_kwargs, scope_context=scope_context
    )
    if scope_name:
        function_name_key = '.'.join([scope_name, function_name])
    else:
        function_name_key = function_name
    return function_name_key


def shared(
    function_=None,
    scope=_get_default_scope,
    scope_context=None,
    scope_kwargs=None,
    timeout=SHARE_DEFAULT_TIMEOUT,
    retries=DEFAULT_CALL_RETRIES,
    function_kw=None,
    inject=False,
    injected_kw='_injected',
):
    r"""Generic function sharing, share the results of any decorated function.
    Any parallel pytest xdist worker will wait for this function to finish

    :type function_: callable
    :type scope: str or callable
    :type scope_kwargs: dict
    :type scope_context: str
    :type timeout: int
    :type retries: int
    :type function_kw: list
    :type inject: bool
    :type injected_kw: str

    :param function_: the function that is intended to be shared
    :param scope: this parameter will define the namespace of data sharing
    :param scope_context: an added context string if applicable, of a concrete
           sharing in combination with scope and function.
    :param scope_kwargs: kwargs to be passed to scope if is a callable
    :param timeout: the time in seconds to wait for waiting the shared function
    :param retries: if the shared function call fail, how much time should
        retry before setting the call with in failure state
    :param function_kw: The function kwargs to use as an additional scope,
        an md5 hexdigest of that kwargs will be created and added to the
        storage scope, that way we should have diffrent stored values for
        diffrent kw values.
    :param inject: whether to recall the function with injecting the result as
        \**kwargs
    :param injected_kw: the kw arg to set to True to inform the function that
        the kwargs was injected from a saved storage
    """
    _check_config()
    class_names = []
    class_name = None
    index = 1
    while class_name != '<module>' and index <= _DEFAULT_CLASS_NAME_DEPTH:
        if class_name:
            class_names.append(class_name)
        class_name = inspect.getouterframes(inspect.currentframe())[index][3]
        index += 1
    class_names.reverse()
    class_name = '.'.join(class_names)
    if function_kw is None:
        function_kw = []

    def main_wrapper(func):
        @functools.wraps(func)
        def function_wrapper(*args, **kwargs):
            function_kw_scope = {key: kwargs.get(key) for key in function_kw}
            function_name = _get_function_name(
                func, class_name=class_name, kwargs=function_kw_scope
            )
            if not ENABLED:
                # if disabled call the function immediately
                return func(*args, **kwargs)

            function_name_key = _get_function_name_key(
                function_name, scope=scope, scope_kwargs=scope_kwargs, scope_context=scope_context
            )
            shared_object = _SharedFunction(
                function_name_key,
                func,
                args=args,
                kwargs=kwargs,
                timeout=timeout,
                retries=retries,
                inject=inject,
                injected_kw=injected_kw,
            )

            return shared_object()

        return function_wrapper

    def wait_function(func):
        return main_wrapper(func)

    if function_:
        return main_wrapper(function_)
    else:
        return wait_function
