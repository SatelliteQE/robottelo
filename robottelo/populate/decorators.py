"""decorators for populate feature"""
from functools import wraps
from robottelo.populate.main import populate, wrap_context


def populate_with(data, context=None, **extra_options):
    """To be used in test cases as a decorator

    Having a data_file like::

        actions:
          - model: Organization
            register: organization_1
            data:
              name: My Org

    Then you can use in decorators::

        @populate_with('file.yaml')
        def test_case_(self):
            'My Org exists in system test anything here'

    And getting the populated entities inside the test_case::

        @populate_with('file.yaml', context=True)
        def test_case_(self, context):
            assert context.entities.organization_1.name == 'My Org'

    You can also set a name to the context argument::

        @populate_with('file.yaml', context='my_context')
        def test_case_(self, my_context):
            assert my_context.organization_1.name == 'My Org'

    """

    def decorator(func):
        """Wrap test method"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """decorator wrapper"""

            result = populate(data, **extra_options)
            if context:
                context_name = context if context is not True else 'context'
                kwargs[context_name] = wrap_context(result)

            return func(*args, **kwargs)

        return wrapper

    return decorator
