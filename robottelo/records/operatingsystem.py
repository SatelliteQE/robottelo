from robottelo.common import records
from robottelo.common.constants import OPERATING_SYSTEMS


class OperatingSystem(records.Record):
    name = records.StringField()
    major = records.IntegerField()
    minor = records.IntegerField()
    family = records.ChoiceField(OPERATING_SYSTEMS)
    release_name = records.StringField(r"osrelease\d\d\d")
