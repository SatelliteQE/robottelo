# coding: utf-8
"""
Tests for robottelo.populate module and commands
"""
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
# def test_org_1(context):
#     """a test with populated data"""
#     assert context.registry['organization_1'].name == "My Organization 1"
#
#
# @populate_with(data_in_dict, context=True, verbose=1)
# def test_org_2(context):
#     """a test with populated data"""
#     assert context.registry['organization_2'].label == "my_organization_2"
#
#
# @populate_with(data_in_string, context=True, verbose=1)
# def test_org_3(context):
#     """a test with populated data"""
#     assert context.registry['organization_3'].name == "My Organization 3"
#     assert context.registry['organization_3'].label == "my_organization_3"
