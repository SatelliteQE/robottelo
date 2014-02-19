from robottelo.api.apicrud import ApiCrud
from robottelo.common import records


class EnvironmentApi(ApiCrud):
    api_path = "/api/environments/"
    api_json_key = u"environment"
    create_fields = ["name"]


class Environment(records.Record):
    name = records.StringField()

    class Meta:
        api_class = EnvironmentApi
