try:
    import redis
except ImportError:
    redis = None

from robottelo.utils.decorators.func_shared.base import BaseStorageHandler

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
LOCK_TIMEOUT = 7200


class RedisStorageHandler(BaseStorageHandler):
    """Redis Key value storage handler"""

    def __init__(
        self,
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        lock_timeout=LOCK_TIMEOUT,
    ):

        self._lock_timeout = lock_timeout
        self._client = redis.StrictRedis(host=host, port=port, db=db, password=password)

    @property
    def client(self):
        return self._client

    def lock(self, key, timeout=None):
        """Return the storage locker context manager"""
        if timeout is None:
            timeout = self._lock_timeout

        lock_key = f'{key}.lock'
        # If acquired the lock will be acquired until release
        return self.client.lock(lock_key, timeout=None, blocking_timeout=timeout)

    def when_lock_acquired(self, lock_object):
        # do nothing
        pass

    def get(self, key):
        """Return the key value

        :type key: str
        """
        value = self.client.get(key)
        if value is not None:
            value = self.decode(value)
        return value

    def set(self, key, value):
        """Write the value of key

        :type key: str
        :type value: object
        """
        value = self.encode(value)
        self.client.set(key, value)
