"""Test class for Content Views

:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: rmynar

:TestType: Functional

:CaseImportance: Medium

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


def _copy_content_export(host, source, dest):
    """ Copies export from export directory to /var/lib/pulp/imports/<dest>
    and sets permissions for pulp.
    Requires full path of source, but only dir name for dest
    """
    return host.execute(
        f"mkdir -p /var/lib/pulp/imports/{dest}/ && "
        f"cp -R {source} /var/lib/pulp/imports/{dest}/ && "
        f"chown -R pulp:pulp /var/lib/pulp/imports/"
    )


def _prepare_supported_repos(product):
    """Create and sync all supported repositories within a given product"""
    repos = dict()

    REPOSITORY_PARAMETERS = {
        'yum_repo': {
            'content-type': 'yum',
            'product-id': product['id'],
            'url': settings.repos.yum_1.url,
        },
        'file_repo': {
            'content-type': 'file',
            'product-id': product['id'],
            'url': settings.repos.file_type_repo.url,
        },
        'ansible_collection_repo': {
            'content-type': 'ansible_collection',
            'product-id': product['id'],
            'url': ANSIBLE_GALAXY,
            'ansible-collection-requirements': '{collections: [ \
                        { name: theforeman.foreman, version: "2.1.0" }, \
                        { name: theforeman.operations, version: "0.1.0"} ]}'
        }
    }

    for repo in REPOSITORY_PARAMETERS:
        repos[repo] = cli_factory.make_repository(REPOSITORY_PARAMETERS[repo])
        Repository.synchronize({'id': repos[repo]['id']})

    return repos


class TestContentExportImportE2E:
    def test_export_import_complete_librany_e2e(self, default_sat):
        """Perform complete Library export. Import the Library and check if
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
            5. Check if Product and Repositories were imported

        :expectedresults: Import Organization contains the same Product and
            repositories as Export Organization

        :CaseAutomation: Automated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        export_org = cli_factory.make_org()

        export_product = cli_factory.make_product({'organization-id': export_org['id']})

        repos = _prepare_supported_repos(export_product)

        ContentExport.completeLibrary({'organization-id': export_org['id']})

        export = ContentExport.list({'organization-id': export_org['id']})

        assert export
        result = _copy_content_export(default_sat, export[0]['path'], export_org['name'])
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
        assert len(import_product['content']) == len(repos)
        for irepo in repos:
            assert repos[irepo]['content-type'] in \
                [repo['content-type'] for repo in import_product['content']]
