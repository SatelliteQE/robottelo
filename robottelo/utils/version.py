# Utility methods and classes related to Satellite/foreman version handling
import json

from packaging.version import Version


def search_version_key(key, value):  # pragma: no cover
    """recursively look for 'version' key and transform it in a Version instance"""
    if key == 'version' and isinstance(value, str):
        return Version(value)
    if isinstance(value, dict):
        return {k: search_version_key(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [search_version_key(key, item) for item in value]
    return value


class VersionEncoder(json.JSONEncoder):  # pragma: no cover
    """Transform Version instances to str"""

    def default(self, z):
        if isinstance(z, Version):
            return str(z)
        return super().default(z)
