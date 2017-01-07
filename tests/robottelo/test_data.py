# # coding: utf-8
# """
# Tests for robottelo.populate module and commands
# """
# from unittest2 import TestCase
# from robottelo.populate import populate_with
#
#
# data_in_dict = {
#     'actions': [
#         {
#             'model': 'Organization',
#             'register': 'organization_1',
#             'data': {
#                 'name': 'My Organization 1',
#                 'label': 'my_organization_1'
#             }
#         },
#         {
#             'model': 'Organization',
#             'register': 'organization_2',
#             'data': {
#                 'name': 'My Organization 2',
#                 'label': 'my_organization_2'
#             }
#         }
#     ]
# }
#
# data_in_string = """
# actions:
#   - model: Organization
#     registry: organization_3
#     data:
#       name: My Organization 3
#       label: my_organization_3
# """
#
#
# @populate_with(data_in_dict, context=True, verbose=1)
# def test_org_1(context=None):
#     """a test with populated data"""
#     assert context.organization_1.name == "My Organization 1"
#
#
# @populate_with(data_in_dict, context=True, verbose=1)
# def test_org_2(context=None):
#     """a test with populated data"""
#     assert context.organization_2.label == "my_organization_2"
#
#
# @populate_with(data_in_string, context=True, verbose=1)
# def test_org_3(**kwargs):
#     """a test with populated data"""
#     context = kwargs['context']
#     assert context.organization_3.name == "My Organization 3"
#     assert context.organization_3.label == "my_organization_3"
#
#
# class MyTestCase(TestCase):
#     """
#     THis test populates data in setUp and also in individual tests
#     """
#     @populate_with(data_in_string, context=True)
#     def setUp(self, context=None):
#         self.context = context
#
#     def test_with_setup_data(self):
#         self.assertEqual(
#             self.context.organization_3.name, "My Organization 3"
#         )
#
#     @populate_with(data_in_dict, context='test_context')
#     def test_with_isolated_data(self, test_context=None):
#         self.assertEqual(
#             test_context.organization_1.name, "My Organization 1"
#         )
