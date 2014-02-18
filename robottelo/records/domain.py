from robottelo.api.apicrud import ApiCrud
from robottelo.common import records

class DomainApi(ApiCrud):
        api_path = "/api/domains/"
        api_json_key = u"domain"
        create_fields = ["name"]

class Domain(records.Record):
    name = records.StringField(format=r"domain\d\d\d\d")

    class Meta:
        api_class = DomainApi

