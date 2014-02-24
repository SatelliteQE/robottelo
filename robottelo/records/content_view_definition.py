from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.organization import Organization


class ContentViewDefinitionApi(ApiCrud):
    api_path = "/katello/api/organizations/:organization.label/content_view_definitions/"  # noqa
    api_json_key = u"content_view_definition"
    create_fields = ["name", "description"]


class ContentViewDefinition(records.Record):
    name = records.basic_positive()
    description = records.basic_positive()
    organization = records.RelatedField(Organization)

    class Meta:
        api_class = ContentViewDefinitionApi
