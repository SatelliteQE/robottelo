from robottelo.api.environments import EnvironmentApi
from robottelo.common import records


class Environments(records.Record):
    name = records.StringField(required=True)

    class Meta:
        api_class = EnvironmentApi
