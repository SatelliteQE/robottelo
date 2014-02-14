from robottelo.api.operating_systems import OperatingSystemApi
from robottelo.common import records
from robottelo.common.constants import OPERATING_SYSTEMS


class OperatingSystem(records.Record):
    name = records.StringField()
    major = records.IntegerField()
    minor = records.IntegerField()
    family = records.ChoiceField(OPERATING_SYSTEMS)
    release_name = records.StringField(r"osrelease\d\d\d")

    class Meta:
        api_class = OperatingSystemApi
