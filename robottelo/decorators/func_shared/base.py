import json


class BaseStorageHandler:
    @staticmethod
    def encode(data):
        return json.dumps(data)

    @staticmethod
    def decode(data):
        return json.loads(data)

    def lock(self, lock_key):
        """Return the storage locker context manager"""
        raise NotImplementedError

    def when_lock_acquired(self, data):
        """called when the lock is acquired to do some added action"""
        raise NotImplementedError

    def get(self, key):
        """Return the key value"""
        raise NotImplementedError

    def set(self, key, value):
        """Write the value of key to storage"""
        raise NotImplementedError
