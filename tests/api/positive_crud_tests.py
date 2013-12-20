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
        ModelApi = self.tested_class()
        model = ModelApi(generate=True)
        response = ModelApi.create(json=model.opts())
        self.assertEqual(response.status_code, self.post_result())
        self.assertFeaturing(model.result_opts(), response.json())

    def test_read_model(self):
        """Basic positive read test"""
        ModelApi = self.tested_class()
        model = ModelApi(generate=True)
        response = ModelApi.create(json=model.opts())
        uid = ModelApi.id_from_json(response.json())

        response = ModelApi.show(uid=uid)
        self.assertEqual(response.status_code, 200)
        self.assertFeaturing(model.result_opts(), response.json())

    def test_read_model_negative(self):
        """We presume that on wrong id, api should return 404"""
        ModelApi = self.tested_class()
        response = ModelApi.show(uid=-1)
        self.assertEqual(response.status_code, 404)

    def test_update_model(self):
        """Basic positive update test"""
        ModelApi = self.tested_class()
        model = ModelApi(generate=True)
        response = ModelApi.create(json=model.opts())
        uid = ModelApi.id_from_json(response.json())
        model = model.change()

        response = ModelApi.update(uid=uid, json=model.opts())
        self.assertEqual(response.status_code, 200)
        self.assertFeaturing(model.result_opts(), response.json())

    def test_remove_model(self):
        """Basic remove test"""
        ModelApi = self.tested_class()
        model = ModelApi(generate=True)
        response = ModelApi.create(json=model.opts())
        uid = ModelApi.id_from_json(response.json())
        response = ModelApi.delete(uid=uid)
        self.assertEqual(response.status_code, 200)
        response = ModelApi.show(uid=uid)
        self.assertEqual(response.status_code, 404)

