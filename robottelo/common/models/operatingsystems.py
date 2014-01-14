from robottelo.common import models
from robottelo.api.operating_systems import OperatingSystemApi
class OperatingSystem(models.Model):
    name = models.StringField(required=True)
    major = models.IntegerField(required = True)
    minor = models.IntegerField(required = True)
    family = models.ChoiceField(
          ["Archlinux",
          "Debian",
          "Freebsd",
          "Gentoo",
          "Redhat",
          "Solaris",
          "Suse",
          "Windows"], required = True)
    release_name = models.StringField(r"osrelease\d\d\d", required = True)

    class Meta:
        api_class = OperatingSystemApi
