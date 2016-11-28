from functools import wraps
from robottelo.data.base import load_data, populate

def populate_with(datafile, **extra_options):

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
