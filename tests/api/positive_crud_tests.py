#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from tests.api.baseapi import BaseAPI

class PositiveCrudTestMixin:

    def tested_class(self):
        raise NotImplementedError("Tested class needs to be defined")

    def post_result(self):
        return 200

    def test_create(self):
        """Create a new model"""
        ModelApi = self.tested_class()
        model = ModelApi(generate=True)
        model = model.filter_create_opts()
        response = ModelApi.create(json=model.opts())
        self.assertEqual(response.status_code, self.post_result())
        self.assertFeaturing(model.result_opts(), response.json())

    def test_read_model(self):
        ModelApi = self.tested_class()
        model = ModelApi(generate=True)
        model = model.filter_create_opts()
        response = ModelApi.create(json=model.opts())
        uid = ModelApi.id_from_json(response.json())

        response = ModelApi.show(uid=uid)
        self.assertEqual(response.status_code, 200)
        self.assertFeaturing(model.result_opts(), response.json())

    def test_read_model_negative(self):
        ModelApi = self.tested_class()
        response = ModelApi.show(uid=-1)
        self.assertEqual(response.status_code, 404)


    def test_update_model(self):
        """Create and update a model"""
        ModelApi = self.tested_class()
        model = ModelApi(generate=True)
        model = model.filter_create_opts()
        response = ModelApi.create(json=model.opts())
        uid = ModelApi.id_from_json(response.json())
        model = model.change()

        response = ModelApi.update(uid=uid,json=model.opts())
        self.assertEqual(response.status_code, 200)
        self.assertFeaturing(model.result_opts(), response.json())

    def test_remove_model(self):
        ModelApi = self.tested_class()
        """Create and update a model"""
        model = ModelApi(generate=True)
        model = model.filter_create_opts()
        response = ModelApi.create(json=model.opts())
        uid = ModelApi.id_from_json(response.json())
        response = ModelApi.delete(uid=uid)
        self.assertEqual(response.status_code, 200)
        response = ModelApi.show(uid=uid)
        self.assertEqual(response.status_code, 404)

