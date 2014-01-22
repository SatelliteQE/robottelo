from robottelo.common import records
from robottelo.api.ptables import PTableApi
from robottelo.common.records.operatingsystems import OperatingSystems
from robottelo.common import conf

class PTables(records.Record):
    name = records.StringField(required=True)
    layout = records.StringField(default="d-i partman-auto/disk", required=True)
    operatingsystem = records.ManyRelatedFields(OperatingSystems,1,3)
    os_family = records.ChoiceField(
          ["Archlinux",
          "Debian",
          "Freebsd",
          "Gentoo",
          "Redhat",
          "Solaris",
          "Suse",
          "Windows"], required = True)

    class Meta:
        api_class = PTableApi
