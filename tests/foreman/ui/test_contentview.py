"""Test class for Content View UI

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""

from airgun.exceptions import NoSuchElementException
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    FAKE_FILE_NEW_NAME,
    REPOS,
    DataFile,
)

VERSION = 'Version 1.0'


@pytest.mark.e2e
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


@pytest.mark.upgrade
def test_positive_delete_cv_promoted_to_multi_env(
    session,
    target_sat,
    module_org,
):
    """Delete the published content view version promoted to multiple
        environments. Delete the entire content view, with a promoted version to
        multiple environments.

    :id: f16f2db5-7f5b-4ebb-863e-6c18ff745ce4

    :steps:
        1. Create and sync yum repository on satellite, add to a new content view.
        2. Publish the content view, 'Version 1.0'
        3. Promote the 'Version 1.0' to multiple environments, Library -> DEV.
        4. Delete the promoted 'Version 1.0', verify removed from environments.
        5. Publish and promote a new 'Version 2.0' to multiple environments.
        6. Delete the entire content view, verify removed from environments.

    :expectedresults: The deleted CVV and CV do not exist in ContentViews UI,
        4. Deleting the single promoted CVV, removed the CV from multiple environments.
        6. Deleting the entire CV containing promoted CVV, removed the CV from multiple environments.

    :CaseImportance: High
    """
    repo = target_sat.cli_factory.RepositoryCollection(
        repositories=[target_sat.cli_factory.YumRepository(url=settings.repos.yum_0.url)]
    )
    repo.setup(module_org.id)
    cv, lce = repo.setup_content_view(module_org.id)
    repo_name = repo.repos_info[0]['name']

    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        cv_info = session.contentview_new.search(cv['name'])[0]
        assert cv_info['Latest version'] == VERSION, (
            f'Latest version for CV {cv["name"]}: {cv_info["Latest version"]},'
            f' does not match expected: {VERSION}.'
        )
        # repo name found in CVV's repositories tab
        assert (
            repo_name
            == session.contentview_new.read_version_table(
                entity_name=cv['name'],
                version=VERSION,
                tab_name='repositories',
            )[0]['Name']
        )
        # Environment's names found in CVV info
        cvv_values = session.contentview_new.read_cv(entity_name=cv['name'], version_name=VERSION)
        assert 'Library' in cvv_values['Environments']
        assert lce['name'] in cvv_values['Environments']
        # CV name is found in both environment's info
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert len(lce_values['content_views']['resources']) == 1
        assert cv['name'] == lce_values['content_views']['resources'][0]['Name']
        library_values = session.lifecycleenvironment.read('Library')
        assert cv['name'] == library_values['content_views']['resources'][0]['Name']

        # Delete the promoted CVV
        session.contentview_new.delete_version(
            entity_name=cv['name'],
            version=VERSION,
        )
        # CVV is no longer found in CV's Versions tab
        with pytest.raises(NoSuchElementException):
            session.contentview_new.read_cv(entity_name=cv['name'], version_name=VERSION)
        # the CV's name is not associated to either environment anymore
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert cv['name'] not in str(lce_values['content_views']['resources'])
        library_values = session.lifecycleenvironment.read('Library')
        assert cv['name'] not in str(library_values['content_views']['resources'])

        # publish & promote, a new Version 2.0, to test deleting entire CV with a CVV promoted to LCEs.
        session.contentview_new.publish(entity_name=cv['name'], promote=True, lce=lce['name'])
        cv_info = session.contentview_new.search(cv['name'])[0]
        assert cv_info['Latest version'] == 'Version 2.0'
        cvv_values = session.contentview_new.read_cv(
            entity_name=cv['name'], version_name='Version 2.0'
        )

        # promotion of CVV added the CV to both environments again
        assert 'Library' in cvv_values['Environments']
        assert lce['name'] in cvv_values['Environments']
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert cv['name'] == lce_values['content_views']['resources'][0]['Name']
        library_values = session.lifecycleenvironment.read('Library')
        assert cv['name'] == library_values['content_views']['resources'][0]['Name']

        # delete the whole content view, search for its name to check
        session.contentview_new.delete(cv['name'])
        assert not session.contentview_new.search(cv['name'])
        # the deleted CV's name is not found in either environment
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert cv['name'] not in str(lce_values['content_views']['resources'])
        library_values = session.lifecycleenvironment.read('Library')
        assert cv['name'] not in str(library_values['content_views']['resources'])


@pytest.mark.upgrade
def test_cv_publish_warning(session, target_sat, function_sca_manifest_org, module_lce):
    """Verify that the publish warning banner accurately reflects the state of a given CV

    :id: 5d6187bf-2f36-46cd-bdfe-dfbda244af39

    :steps:
        1. Create and sync yum repository on satellite, add to a new content view.
        2. Check the publish wizard, and verify that the publish warning banner is visible
        3. Publish the CV
        4. Check the publish wizard again for the CV and verify the warning isn't visible

    :expectedresults: The publish warning banner accurately reflects the status of the CV

    :Verifies: SAT-28271

    :customerscenario: true

    :CaseImportance: High
    """
    rh_repo_id = target_sat.api_factory.enable_sync_redhat_repo(
        REPOS['rhae2.9_el8'], function_sca_manifest_org.id
    )
    rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
    cv = target_sat.api.ContentView(organization=function_sca_manifest_org).create()
    cv = target_sat.api.ContentView(id=cv.id, repository=[rh_repo]).update(["repository"])
    with target_sat.ui_session() as session:
        session.organization.select(org_name=function_sca_manifest_org.name)
        assert not session.contentview_new.check_publish_banner(cv.name)
        cv.publish()
        assert session.contentview_new.check_publish_banner(cv.name)


def test_cv_lce_order(session, module_target_sat, function_sca_manifest_org, module_lce):
    """Verify that LCEs are displayed in Path order in the UI

    :id: f6a7df48-d4ca-405f-8b31-bda4865e3329

    :steps:
        1. Create multiple LCEs in a specific path order.
        2. Create and promote a CV to all the LCEs.
        3. Check the UI for that CV Version.

    :expectedresults: The LCEs are displayed in path order.

    :Verifies: SAT-28538

    :customerscenario: true

    :CaseImportance: High
    """
    lce1 = module_target_sat.api.LifecycleEnvironment(
        organization=function_sca_manifest_org
    ).create()
    lce2 = module_target_sat.api.LifecycleEnvironment(
        organization=function_sca_manifest_org, prior=lce1
    ).create()
    lce3 = module_target_sat.api.LifecycleEnvironment(
        organization=function_sca_manifest_org, prior=lce2
    ).create()
    lce4 = module_target_sat.api.LifecycleEnvironment(
        organization=function_sca_manifest_org, prior=lce3
    ).create()
    cv = module_target_sat.api.ContentView(organization=function_sca_manifest_org).create()
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=function_sca_manifest_org.name)
        results = session.contentview_new.publish(
            entity_name=cv.name,
            promote=True,
            multi_promote=True,
            lce={
                f"{lce1.name}": True,
                f"{lce2.name}": True,
                f"{lce3.name}": True,
                f"{lce4.name}": True,
            },
        )
        # Stripping results string of the timestamp from the chips
        formatted_lces = (
            results[0]['Environments']
            .replace('less than a minute ago', '')
            .replace('1 minute ago', '')
        )
        assert formatted_lces == f"Library  {lce1.name}  {lce2.name}  {lce3.name}  {lce4.name} "
