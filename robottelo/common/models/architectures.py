from robottelo.common import models
from robottelo.api.architectures import ArchitectureApi

class Architectures(models.Model):
    name = models.StringField(required=True)

    class Meta:
        api_class = ArchitectureApi
