from robottelo.common import models
from robottelo.api.domains import DomainApi

class Domains(models.Model):
    name = models.StringField(required=True)

    class Meta:
        api_class = DomainApi
