"""
It is not meant to be used directly, but as part of a robottelo.hosts.Satellite instance
example: my_satellite.api_factory.api_method()
"""


class APIFactory:
    """This class is part of a mixin and not to be used directly. See robottelo.hosts.Satellite"""

    def __init__(self, satellite):
        self._satellite = satellite
