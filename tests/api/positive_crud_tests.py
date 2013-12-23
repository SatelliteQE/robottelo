# -*- encoding: utf-8 -*-

"""
Module for automatic implementation of positive crud tests.
"""


class PositiveCrudTestMixin(object):
    """Implements basic crud tests based oon supplied test class
    implementing ApiCrudMixin and ApiModelMixin

    """

    def __init__(self):
        """Mixin is not to be instantiated"""
        raise NotImplementedError("Mixin is not to be instantiated")

    def tested_class(self):
        """Returns class implementing both ApiCrudMixin and ApiModelMixin"""
        raise NotImplementedError("Tested class needs to be defined")

    def post_result(self):
        """Override might be required for some endpoint,
        i.e POST /api/models returns 201 on success"""
        return 200

    def test_create(self):
        """Basic positive create test"""
        model_api = self.tested_class()
        model = model_api(generate=True)
        response = model_api.create(json=model.opts())
        self.assertEqual(response.status_code, self.post_result())
        self.assertFeaturing(model.result_opts(), response.json())

    def test_read_model(self):
        """Basic positive read test"""
        model_api = self.tested_class()
        model = model_api(generate=True)
        response = model_api.create(json=model.opts())
        uid = model_api.id_from_json(response.json())

        response = model_api.show(uid=uid)
        self.assertEqual(response.status_code, 200)
        self.assertFeaturing(model.result_opts(), response.json())

    def test_read_model_negative(self):
        """We presume that on wrong id, api should return 404"""
        model_api = self.tested_class()
        response = model_api.show(uid=-1)
        self.assertEqual(response.status_code, 404)

    def test_update_model(self):
        """Basic positive update test"""
        model_api = self.tested_class()
        model = model_api(generate=True)
        response = model_api.create(json=model.opts())
        uid = model_api.id_from_json(response.json())
        model = model.change()

        response = model_api.update(uid=uid, json=model.opts())
        self.assertEqual(response.status_code, 200)
        self.assertFeaturing(model.result_opts(), response.json())

    def test_remove_model(self):
        """Basic remove test"""
        model_api = self.tested_class()
        model = model_api(generate=True)
        response = model_api.create(json=model.opts())
        uid = model_api.id_from_json(response.json())
        response = model_api.delete(uid=uid)
        self.assertEqual(response.status_code, 200)
        response = model_api.show(uid=uid)
        self.assertEqual(response.status_code, 404)
