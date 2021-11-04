"""Test class for Content Views

:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: rmynar

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os.path
from robottelo.cli import factory as cli_factory
from robottelo.cli.content_export import ContentExport
from robottelo.cli.content_import import ContentImport
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.config import settings
from robottelo.constants.repos import ANSIBLE_GALAXY


class TestContentExportImportE2E:
    def test_export_import_complete_librany_e2e(self, default_sat):
        """Perform complete library export. Import the library and check if
        the import went ok.

        :Setup:
            1. Create Organization
            2. Create Product
            3. Create Repositories and synchronize

        :Steps:
            1. Export Organization content
            2. Copy exported data into import directory
            3. Create another Organization
            4. Import data
            5. Check if Product and Repositories were inported

        :expectedresults: Imported Organization contains the same Product and
            repositories as Export Organization

        :CaseAutomation: Automated

        :CaseLevel: Integration

        :CaseImportance: High
        """
        export_org = cli_factory.make_org()

        export_product = cli_factory.make_product({'organization-id': export_org['id']})

        yum_repo = cli_factory.make_repository(
            {
                'content-type': 'yum',
                'product-id': export_product['id'],
                'url': settings.repos.yum_1.url,
            }
        )
        file_repo = cli_factory.make_repository(
            {
                'content-type': 'file',
                'product-id': export_product['id'],
                'url': settings.repos.file_type_repo.url,
            }
        )
        ansible_collection_repo = cli_factory.make_repository(
            {
                'content-type': 'ansible_collection',
                'product-id': export_product['id'],
                'url': ANSIBLE_GALAXY,
                'ansible-collection-requirements': '{collections: [ \
                            { name: theforeman.foreman, version: "2.1.0" }, \
                            { name: theforeman.operations, version: "0.1.0"} ]}'
            }
        )

        # ansible_repo = cli_factory.make_repository({'product-id': module_product.id})
        # file_repo = cli_factory.make_repository({'product-id': module_product.id})
        Repository.synchronize({'id': yum_repo['id']})
        Repository.synchronize({'id': file_repo['id']})
        Repository.synchronize({'id': ansible_collection_repo['id']})

        ContentExport.completeLibrary({'organization-id': export_org['id']})
        # export_path = export['message']

        export = ContentExport.list({'organization-id': export_org['id']})

        assert export
        result = default_sat.execute(
            f"mkdir -p /var/lib/pulp/imports/{export_org['name']}/ && "
            f"cp -R {export[0]['path']} /var/lib/pulp/imports/{export_org['name']}/ && "
            f"chown -R pulp:pulp /var/lib/pulp/imports/"
            )
        assert result.status == 0

        import_org = cli_factory.make_org()
        ContentImport.library(
            {
                'organization-id': import_org['id'],
                'path': f"/var/lib/pulp/imports/{export_org['name']}/"
                        f"{os.path.basename(export[0]['path'])}/"
            }
        )

        assert Product.list({'organization-id': import_org['id']})

        import_product = Product.info(
            {
                'organization-id': import_org['id'],
                'id': Product.list({'organization-id': import_org['id']})[0]['id']
            }
        )
        assert import_product['name'] == export_product['name']
        assert len(import_product['content']) == 3
        assert "yum" in [repo['content-type'] for repo in import_product['content']]
        assert "file" in [repo['content-type'] for repo in import_product['content']]
        assert "ansible_colelction" in [repo['content-type'] for repo in import_product['content']]