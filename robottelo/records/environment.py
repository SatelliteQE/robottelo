from robottelo.api.environments import EnvironmentApi
from robottelo.common import records


class Environment(records.Record):
    name = records.StringField()

    class Meta:
        api_class = EnvironmentApi

