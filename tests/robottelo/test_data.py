from robottelo.populate import populate_with


# def test_decorator_loads_data():
#
#     @populate_with('test_data.yaml')
#     def test_anything():
#         """Simple function"""
#
#     test_anything()


@populate_with('test_data.yaml')
def test_entities_presence():
    """entities should be present"""