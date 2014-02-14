# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrud


class OrganizationApi(ApiCrud):
       api_path = "/katello/api/organizations/"
       api_json_key = u"organization"
       create_fields = ["name", "label", "description"]


