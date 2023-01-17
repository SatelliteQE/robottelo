import os
import tempfile

from pytest_services.locks import file_lock

from robottelo.config import settings
from robottelo.utils.decorators.func_shared.base import BaseStorageHandler

TEMP_ROOT_DIR = 'robottelo'
TEMP_FUNC_SHARED_DIR = 'shared_functions'
SHARED_DIR = None


LOCK_TIMEOUT = 7200


def get_temp_dir():
    tmp_dir = settings.robottelo.tmp_dir
    if not tmp_dir:
        tmp_dir = tempfile.gettempdir()
    return tmp_dir


def _get_root_dir(create=True):
    global SHARED_DIR
    if SHARED_DIR is not None:
        return SHARED_DIR

    tmp_root_dir = os.path.join(get_temp_dir(), TEMP_ROOT_DIR, TEMP_FUNC_SHARED_DIR)
    if create and not os.path.exists(tmp_root_dir):
        try:
            # it can happen that the workers try to create this path at the
            # same time
            os.makedirs(tmp_root_dir)
        except OSError:
            if not os.path.exists(tmp_root_dir):
                raise

    SHARED_DIR = tmp_root_dir

    return SHARED_DIR


class FileStorageHandler(BaseStorageHandler):
    """Key value file storage handler."""

    def __init__(self, root_dir=None, create=True, lock_timeout=LOCK_TIMEOUT):

        if root_dir is None:
            root_dir = _get_root_dir()

        if create and not os.path.exists(root_dir):
            os.makedirs(root_dir)

        self._lock_timeout = lock_timeout
        self._root_dir = root_dir

    @property
    def root_dir(self):
        return self.root_dir()

    def get_key_file_path(self, key):
        return os.path.join(self._root_dir, key)

    def lock(self, key):
        """Return the storage locker context manager"""
        lock_key = f'{key}.lock'
        return file_lock(self.get_key_file_path(lock_key), remove=False, timeout=self._lock_timeout)

    def when_lock_acquired(self, handler):
        """Write the process id to file handler"""
        handler.seek(0)
        handler.truncate()
        handler.write(str(os.getpid()))
        handler.flush()

    def get(self, key):
        """Return the key value
        :type key: str
        """
        value = None
        key_file_path = self.get_key_file_path(key)
        if os.path.exists(key_file_path):
            with open(key_file_path) as file_handler:
                value = file_handler.read()

        if value is not None:
            value = self.decode(value)
        return value

    def set(self, key, value):
        """Write the value of key

        :type key: str
        :type value: object
        """
        value = self.encode(value)
        key_file_path = self.get_key_file_path(key)
        with open(key_file_path, 'w') as file_handler:
            file_handler.write(value)
