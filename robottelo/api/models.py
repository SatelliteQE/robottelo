# -*- encoding: utf-8 -*-
from robottelo.api.apicrud import ApiCrudMixin
from robottelo.api.model import ApiModelMixin
from robottelo.common.helpers import generate_name


class ModelApi(ApiCrudMixin, ApiModelMixin):
    """Implementation of /api/models endpoint"""
    @classmethod
    def api_path(cls):
        return "/api/models/"

    @classmethod
    def id_from_json(cls, json):
        """Required for automatic generating of crud tests"""
        return json[u'model'][u'id']

    def __init__(self, generate=False):
        """Generates valid model for crud operations"""
        if generate:
            self.name = unicode(generate_name(8))
            self.info = unicode(generate_name(8))
            self.vendor_class = unicode(generate_name(8))
            self.hardware_model = unicode(generate_name(8))

    def opts(self):
        return {u'model': self.to_data_structure()}

    def change(self):
        self.info += "updated"
        return self
