from robottelo.datafactory import gen_string


def test_positive_create(session):
    cv_name = gen_string('alpha')
    label = gen_string('alpha')
    description = gen_string('alpha')
    with session:
        session.contentview.create({
            'name': cv_name,
            'label': label,
            'description': description,
        })
        assert session.contentview.search(cv_name) == cv_name
        cv_values = session.contentview.read(cv_name)
        assert cv_values['Details']['name'] == cv_name
        assert cv_values['Details']['label'] == label
        assert cv_values['Details']['description'] == description
        assert cv_values['Details']['composite'] == 'No'
