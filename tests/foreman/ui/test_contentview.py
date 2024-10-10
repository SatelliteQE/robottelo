"""Test class for Content View UI

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    FAKE_FILE_NEW_NAME,
    REPOS,
    DataFile,
)


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


# @pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_delete_cv_promoted_to_multi_env(
    session,
    module_target_sat,
    module_org,
    target_sat,
):
    """Delete the published content view and the version promoted to multiple
        environments.

    :id: f16f2db5-7f5b-4ebb-863e-6c18ff745ce4

    :steps:
        1. Create a yum repo on satellite
        2. Create a content view and add the repository
        3. Publish the content view, creates "Version 1.0"
        4. Promote the "Version 1.0" to multiple environments Library -> DEV
        5. Delete the promoted content view version
        6. Publish and promote a new "Version 1.0" to multiple environments
        7. Delete the content view

    :expectedresults:
        5. Deleting the promoted CVV, removed the CV from multiple environments.
        7. Deleting the CV with promoted CVV, removed the CV from multiple environments.

    :CaseImportance: High
    """
    VERSION = 'Version 1.0'
    repo = target_sat.cli_factory.RepositoryCollection(
        repositories=[target_sat.cli_factory.YumRepository(url=settings.repos.yum_0.url)]
    )
    repo.setup(module_org.id)
    cv, lce = repo.setup_content_view(module_org.id)
    repo_name = repo.repos_info[0]['name']

    with target_sat.ui_session() as session:
        # session.location.select(loc_name=DEFAULT_LOC)
        session.organization.select(org_name=module_org.name)
        cv_info = session.contentview_new.search(cv['name'])[0]
        assert cv_info['Latest version'] == VERSION, (
            f'Latest version for CV {cv["name"]}: {cv_info["Latest version"]},'
            f' does not match expected: {VERSION}.'
        )
        cvv_values = session.contentview_new.read_cv(cv['name'], VERSION)
        assert lce['name'] in cvv_values['Environments']
        # read UI info from repo table in CVV
        repo_info = session.contentview_new.read_version_table(cv['name'], VERSION, 'repositories')
        assert (
            repo_name == repo_info[0]['Name']
        ), 'Repositories tab for CVV shows incorrect repo name.'
        # read UI info from LCE of the CVV
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert len(lce_values['content_views']['resources']) == 1
        assert (
            cv['name'] == lce_values['content_views']['resources'][0]['Name']
        ), f'Environment {lce["name"]}, does not show expected CVV {cv["name"]}, contained within.'
        # delete the CVV, try searching for it, then delete the ContentView itself
        session.contentview_new.click_version_dropdown(cv['name'], VERSION, 'Delete')
        # session.contentview.remove_version(cv['name'], VERSION, False, [ENVIRONMENT, lce['name']])
        cv = session.contentview_new.search(cv['name'], VERSION)[0]
        """assert lce['name'] not in cv['Environments']
        assert 'Library' not in cv['Environments']"""
        session.contentview.delete(cv['name'])
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert cv not in lce_values['content_views']['resources']
