# -*- encoding: utf-8 -*-
from apicrud import ApiCrudMixin
from model import ApiModelMixin
from random import randint, choice
from lib.common.helpers import generate_name
from lib.common.helpers import generate_email_address

class ModelApi(ApiCrudMixin,ApiModelMixin):
    """Implementation of /api/operatingsystems endpoint"""
    @classmethod
    def api_path(cls):
        return "/api/models/"

    @classmethod
    def id_from_json(cls, json):
        return json[u'model'][u'id']

    def __init__(self, generate=False):
        if generate:
            self.name = unicode(generate_name(8))
            self.info = unicode(generate_name(8))
            self.vendor_class = unicode(generate_name(8))
            self.hardware_model = unicode(generate_name(8))

    def filter_create_opts(self,**kwargs):
        temp = self.copy()
        return temp

    def opts(self):
        return {u'model':self.to_json()}

    def result_opts(self):
        return self.opts()

    def change(self):
        self.info+="updated"
        return self
