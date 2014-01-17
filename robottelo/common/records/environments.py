from robottelo.common import records
from robottelo.api.environments import EnvironmentApi

class Environments(records.Record):
    name = records.StringField(required=True)

    class Meta:
        api_class = EnvironmentApi
