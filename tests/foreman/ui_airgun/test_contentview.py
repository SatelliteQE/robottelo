from nailgun import entities

from robottelo.datafactory import gen_string
from robottelo.decorators import tier2


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


@tier2
def test_positive_add_custom_content(session):
    """Associate custom content in a view

    :id: 7128fc8b-0e8c-4f00-8541-2ca2399650c8

    :setup: Sync custom content

    :expectedresults: Custom content can be seen in a view

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    product = entities.Product(organization=org).create()
    entities.Repository(name=repo_name, product=product).create()
    with session:
        session.organization.select(org_name=org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name) == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        cv_values = session.contentview.read(cv_name)
        assert cv_values['yumrepo']['repos']['assigned'][0] == repo_name
