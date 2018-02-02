from airgun.decorators import parametrize
from robottelo.datafactory import valid_data_list


@parametrize('name', valid_data_list())
def test_positive_create(session, name):
    with session:
        session.architecture.create_architecture({'name': name})
