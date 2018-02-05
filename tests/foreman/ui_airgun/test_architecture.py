from robottelo.datafactory import valid_data_list
from robottelo.decorators import parametrize


@parametrize('name', valid_data_list())
def test_positive_create(session, name):
    with session:
        session.architecture.create_architecture({'name': name})
