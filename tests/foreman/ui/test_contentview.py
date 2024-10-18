"""Test class for Content View UI

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.constants import FAKE_FILE_NEW_NAME, REPOS, DataFile

VERSION = 'Version 1.0'


@pytest.mark.e2e
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_target_sat, module_org, module_lce):
    """Create content view with yum repo, publish it and promote it to Library

    :id: 0970db8d-e9e3-4317-8703-153a6d9b2875

    :steps:
        1. Create Product/repo and Sync it
        2. Create CV and add created repo in step1
        3. Publish and promote it to new LCE

    :expectedresults: content view is created, updated with repo publish and
        promoted to  the LCE

    """
    repo_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    # Creates a CV along with product and sync'ed repository
    module_target_sat.api_factory.create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.contentview_new.create({'name': cv_name})
        session.contentview_new.add_content(cv_name, repo_name)
        result = session.contentview_new.publish(cv_name, promote=True, lce=module_lce.name)
        assert result[0]['Version'] == VERSION
        assert module_lce.name in result[0]['Environments']


@pytest.mark.e2e
@pytest.mark.tier2
def test_positive_ccv_e2e(session, module_target_sat, module_org, module_lce):
    """Create several CVs, and a CCV. Associate some content with each, and then associate the CVs
    with the CCV - everything should work properly.

    :id: d2db760d-4441-4e6e-9f7d-84501d8e0a13

    :steps:
        1. Create Product/repo and Sync it
        2. Create Composite CV
        3. Create 3 Component CV and add the created Repo.
        4. Publish and promote them to new LCE
        5. Add all 3 to the Composite CV, and publish.

    :expectedresults: CCV can be created, and CVs can be added to it. Repository count is appropriate.
    """
    ccv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    # Create a product and sync'ed repository
    module_target_sat.api_factory.create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with module_target_sat.ui_session() as session:
        # Creates a composite CV
        session.organization.select(org_name=module_org.name)
        session.contentview_new.create({'name': ccv_name}, composite=True)
        # Create three content-views and add synced repo to them
        for _ in range(3):
            cv_name = module_target_sat.api.ContentView(organization=module_org).create().name
            session.contentview_new.add_content(cv_name, repo_name)
            session.contentview_new.publish(cv_name, promote=True, lce=module_lce.name)
            result = session.contentview_new.add_cv(ccv_name, cv_name)
            assert result[0]['Status'] == 'Added'
        session.contentview_new.publish(ccv_name)
        # Check that composite cv has one repository in the table as we
        # were using the same repository for each Content View.
        result = session.contentview_new.read_version_table(ccv_name, VERSION, 'repositories')
        assert len(result) == 1


@pytest.mark.tier2
def test_positive_create_cv(session, target_sat):
    """Able to create cv and search for it

    :id: 15666f4e-d6e6-448a-97df-fede20cc2d1a

    :steps:
        1. Create a CV in the UI
        2. Search for the CV

    :expectedresults: CV is visible in the UI, and matches the given name

    :CaseImportance: High
    """
    cv = gen_string('alpha')
    with target_sat.ui_session() as session:
        session.contentview_new.create(dict(name=cv))
        assert session.contentview_new.search(cv)[0]['Name'] == cv


@pytest.mark.tier2
def test_version_table_read(session, function_sca_manifest_org, target_sat):
    """Able to read CV version package details, which includes the Epoch tab

    :id: fe2a87c7-f148-40f2-b11a-c209a4807016

    :steps:
        1. Enable and Sync RHEL8 Base OS Repo
        2. Add repo to a CV
        3. Publish the CV
        4. Navigate to the published Version's page
        5. Filter packages to only an arbitrary package

    :expectedresults: The package is present, has the appropriate name, and has the epoch tab present

    :CaseImportance: Critical

    :BZ: 1911545

    :customerscenario: true
    """
    rh_repo_id = target_sat.api_factory.enable_sync_redhat_repo(
        REPOS['rhae2.9_el8'], function_sca_manifest_org.id
    )
    rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
    packages = target_sat.api.Repository(id=rh_repo_id).packages()
    cv = target_sat.api.ContentView(organization=function_sca_manifest_org).create()
    cv = target_sat.api.ContentView(id=cv.id, repository=[rh_repo]).update(["repository"])
    cv.publish()
    with target_sat.ui_session() as session:
        session.organization.select(org_name=function_sca_manifest_org.name)
        response = session.contentview_new.read_version_table(
            cv.name, 'Version 1.0', 'rpmPackages', search_param=packages['results'][0]['nvra']
        )
        assert response[0]['Epoch'] == packages['results'][0]['epoch']
        assert response[0]['Name'] == packages['results'][0]['nvra']
        assert response[0]['Version'] == packages['results'][0]['version']
        assert response[0]['Release'] == packages['results'][0]['release']
        assert response[0]['Arch'] == packages['results'][0]['arch']


@pytest.mark.tier2
def test_no_blank_page_on_language_switch(session, target_sat, module_org):
    """Able to view the new CV UI when the language is set to something other
    than English

    :id: d8745aca-b199-4c7e-a970-b1f0f5c5d56c

    :steps:
        1. Change the Satellite system language to French
        2. Attempt to view the CV UI, and read the CV table

    :expectedresults: CV UI is visible, and isn't a blank page

    :BZ: 2163538

    :customerscenario: true
    """
    user_password = gen_string('alpha')
    user = target_sat.api.User(
        default_organization=module_org,
        organization=[module_org],
        password=user_password,
        admin=True,
    ).create()
    cv = target_sat.api.ContentView(organization=module_org).create()
    cv.publish()
    with target_sat.ui_session(user=user.login, password=user_password) as session:
        session.user.update(user.login, {'user.language': 'Français'})
        assert session.contentview_new.read_french_lang_cv()


@pytest.mark.tier2
def test_file_cv_display(session, target_sat, module_org, module_product):
    """Content-> Files displays only the Content Views associated with that file

    :id: 41719f2f-2170-4b26-b65f-2063a1eac7fb

    :steps:
        1. Create a file repo, and upload content into it
        2. Add file repo to a CV, and publish it
        3. Create another CV, and publish it
        4. Navigate to the Content -> File section of the UI

    :expectedresults: Only the Content View with the file repo is displayed.

    :BZ: 2026701

    :customerscenario: true

    :Verifies: SAT-17081
    """
    repo_name = gen_string('alpha')
    file_repo = target_sat.api.Repository(
        product=module_product, name=f'{repo_name}_file_repo', content_type='file'
    ).create()
    with open(DataFile.FAKE_FILE_NEW_NAME, 'rb') as handle:
        file_repo.upload_content(files={'content': handle})
    assert file_repo.read().content_counts['file'] == 1
    cv = target_sat.api.ContentView(organization=module_org).create()
    cv = target_sat.api.ContentView(id=cv.id, repository=[file_repo]).update(['repository'])
    cv.publish()
    cv2 = target_sat.api.ContentView(organization=module_org).create()
    cv2.publish()
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        file_values = session.file.read_cv_table(FAKE_FILE_NEW_NAME)
        assert len(file_values) == 1
        assert file_values[0]['Name'] == cv.name
