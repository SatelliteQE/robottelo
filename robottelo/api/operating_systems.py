# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrud


class OperatingSystemApi(ApiCrud):
        api_path = "/api/operatingsystems"
        api_json_key = u"operatingsystem"

        create_fields = ["name",
                         "major",
                         "minor",
                         "family",
                         "release_name"]
