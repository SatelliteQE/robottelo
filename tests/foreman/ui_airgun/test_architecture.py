from fauxfactory import gen_string

from airgun.decorators import parametrize
from airgun.fixtures import session


def valid_data_list():
    """Generates a list of valid input values."""
    return [
        gen_string('alphanumeric', 25),
        gen_string('alpha', 15),
    ]


@parametrize('name', valid_data_list())
def test_positive_create(session, name):
    with session:
        session.architecture.create_architecture({'name': name})
