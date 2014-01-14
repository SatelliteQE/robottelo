from robottelo.common import models
from robottelo.api.environments import EnvironmentApi

class Environments(models.Model):
    name = models.StringField(required=True)

    class Meta:
        api_class = EnvironmentApi
