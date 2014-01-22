from robottelo.common import records
from robottelo.api.operating_systems import OperatingSystemApi
class OperatingSystems(records.Record):
    name = records.StringField(required=True)
    major = records.IntegerField(required = True)
    minor = records.IntegerField(required = True)
    family = records.ChoiceField(
          ["Archlinux",
          "Debian",
          "Freebsd",
          "Gentoo",
          "Redhat",
          "Solaris",
          "Suse",
          "Windows"], required = True)
    release_name = records.StringField(r"osrelease\d\d\d", required = True)

    class Meta:
        api_class = OperatingSystemApi
