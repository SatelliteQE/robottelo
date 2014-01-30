from robottelo.common import records
from robottelo.common.constants import OPERATING_SYSTEMS


def default_value():
    return 'defaultfromcallable'


class SampleRecord(records.Record):
    name = records.StringField()
    major = records.IntegerField()
    minor = records.IntegerField()
    os_family = records.ChoiceField(OPERATING_SYSTEMS)
    release_name = records.StringField(r"release\d\d\d")
    field_with_default = records.StringField(default='mydefault')
    callable_default = records.StringField(default=default_value)

    def _post_init(self):
        """Some post init processing"""
        setattr(self, 'post_init_var', True)

    class Meta:
        api_path = "/api/operatingsystems"
        api_json_key = u"operatingsystem"
