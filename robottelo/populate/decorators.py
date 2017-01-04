"""decorators for populate feature"""
from functools import wraps
from robottelo.populate.main import load_data, populate


def populate_with(datafile, **extra_options):
    """To be used in test cases as a decorator::

        @populate_with('file.yaml')
        def test_case_():
            'test anything'

    So before the case below is executed, the system
    is populated with the data defined in file.yaml
    """

    def decorator(func):
        """Wrap test method"""

        data = load_data(datafile)

        @wraps(func)
        def wrapper(*args, **kwargs):
            """decorator wrapper"""

            populate(data, **extra_options)

            return func(*args, **kwargs)

        return wrapper

    return decorator
