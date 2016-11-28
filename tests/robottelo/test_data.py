from robottelo.data import populate_with


def test_decorator_loads_data():

    @populate_with('test_data.yaml')
    def data_is_loaded():
        pass

    data_is_loaded()
