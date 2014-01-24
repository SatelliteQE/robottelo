from robottelo.common import records


def default_value():
    return 'defaultfromcallable'


class SampleRecord(records.Record):
    name = records.StringField(required=True)
    major = records.IntegerField(required=True)
    minor = records.IntegerField(required=True)
    os_family = records.ChoiceField([
        "Archlinux",
        "Debian",
        "Freebsd",
        "Gentoo",
        "Redhat",
        "Solaris",
        "Suse",
        "Windows"
    ], required=True)
    release_name = records.StringField(r"release\d\d\d", required=True)
    field_with_default = records.StringField(default='mydefault')
    callable_default = records.StringField(default=default_value)

    def _post_init(self):
        """Some post init processing"""
        setattr(self, 'post_init_var', True)

    class Meta:
        api_path = "/api/operatingsystems"
        api_json_key = u"operatingsystem"
