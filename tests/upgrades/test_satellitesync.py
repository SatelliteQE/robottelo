"""Test for Inter Satellite Sync related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: InterSatelliteSync

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data

from robottelo import ssh
from robottelo.cli.contentview import ContentView
from robottelo.cli.package import Package
from robottelo.test import CLITestCase


class scenario_preversion_cv_exports_imports(CLITestCase):
    """Test Content-view created before upgrade can be exported and imported after upgrade

        Test Steps:

        1. Before upgrade, Create a ContentView
        2. Publish and promote the CV
        3. Upgrade the satellite
        4. Post upgrade, Export and Import the Content Views version created before upgrade

        :expectedresults: Content-view created before upgrade should be exported and imported
            after upgrade
     """
    export_base = '/var/lib/pulp/katello-export/'

    def tearDownScenario(self):
        """Removes CV export file/directory from export base directory"""
        ssh.command('rm -rf {}/*'.format(self.export_base))

    def set_importing_org(self, product, repo, cv):
        """Sets same CV, product and repository in importing organization as
        exporting organization

        :param str product: The product name same as exporting product
        :param str repo: The repo name same as exporting repo
        :param str cv: The cv name same as exporting cv
        """
        self.importing_org = entities.Organization().create()
        self.importing_prod = entities.Product(
            organization=self.importing_org, name=product).create()
        self.importing_repo = entities.Repository(
            name=repo, mirror_on_sync='no',
            download_policy='immediate', product=self.importing_prod).create()
        self.importing_cv = entities.ContentView(
            name=cv, organization=self.importing_org).create()
        self.importing_cv.repository = [self.importing_repo]
        self.importing_cv.update(['repository'])

    @pre_upgrade
    def test_pre_version_cv_export_import(self):
        """Create Content view and publish promote it

        :id: preupgrade-f19e4928-94db-4df6-8ce8-b5e4afe34258

        :steps:

        1. Before upgrade, Create a ContentView
        2. Publish and promote the Content View

        :expectedresults: content view should be published and promoted
        """
        exporting_cv_name = gen_string('alphanumeric')
        exporting_prod_name = gen_string('alphanumeric')
        exporting_repo_name = gen_string('alphanumeric')
        org = entities.Organization().create()
        product = entities.Product(organization=org, name=exporting_prod_name).create()
        repo = entities.Repository(
            product=product, name=exporting_repo_name,
            mirror_on_sync=False, download_policy='immediate').create()
        repo.sync()
        cv = entities.ContentView(name=exporting_cv_name, organization=org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        self.assertTrue(cv.version[0].read().package_count > 0)
        scenario_facts = {self.__class__.__name__: {
            'exporting_orgid': org.id,
            'exporting_cvname': exporting_cv_name,
            'exporting_prodname': exporting_prod_name,
            'exporting_reponame': exporting_repo_name}}
        create_dict(scenario_facts)

    @post_upgrade(depend_on=test_pre_version_cv_export_import)
    def test_post_version_cv_export_import(self):
        """Export and Import cv version created before upgrade

        :id: postupgrade-f19e4928-94db-4df6-8ce8-b5e4afe34258

        :steps: Export and Import the Content Views version created before upgrade

        :expectedresults: Content-view created before upgrade should be exported and imported
            after upgrade
         """
        prescene_dict = get_entity_data(self.__class__.__name__)
        exporting_cv = entities.ContentView(organization=prescene_dict['exporting_orgid']).search(
            query={'search': 'name={}'.format(prescene_dict['exporting_cvname'])})[0]
        exporting_cvv_id = max([cvv.id for cvv in exporting_cv.version])
        exporting_cvv_version = entities.ContentViewVersion(id=exporting_cvv_id).read().version
        ContentView.version_export(
            {'export-dir': '{}'.format(self.export_base), 'id': exporting_cvv_id})
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, exporting_cv.name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        exported_packages = Package.list({'content-view-version-id': exporting_cvv_id})
        self.assertTrue(len(exported_packages) > 0)
        self.set_importing_org(
            prescene_dict['exporting_prodname'], prescene_dict['exporting_reponame'],
            exporting_cv.name)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': self.importing_org.id
        })
        importing_cvv = self.importing_cv.read().version
        self.assertTrue(len(importing_cvv) == 1)
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0].id})
        self.assertTrue(len(imported_packages) > 0)
        self.assertEqual(len(exported_packages), len(imported_packages))
        self.tearDownScenario()
