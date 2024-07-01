"""Build Validation tests

:Requirement: Sanity

:CaseAutomation: Automated

:CaseComponent: BVT

:Team: JPL

:CaseImportance: Critical

"""

import re

import pytest

from robottelo.config import settings
from robottelo.utils.ohsnap import ohsnap_snap_rpms

pytestmark = [pytest.mark.build_sanity]


def test_installed_packages_with_versions(target_sat):
    """Compare the packages that suppose to be installed from repo vs installed packages

    :id: 08913caa-5084-444f-a37d-63da205acc74

    :expectedresults: All the satellite packages and their installed versions should be
        identical to ohsnap as SOT
    """
    # Raw Data from Ohsnap and Satellite Server
    ohsnap_rpms = ohsnap_snap_rpms(
        ohsnap=settings.ohsnap,
        sat_version=settings.server.version.release,
        snap_version=settings.server.version.snap,
        os_major=settings.server.version.rhel_version,
    )
    # Suggested Comment:
    # rpm -qa --queryformat "<you-choose-the-format>"
    installed_rpms = target_sat.execute('rpm -qa').stdout
    installed_rpms = installed_rpms.splitlines()

    # Changing both the datas to comparable formats

    # Formatting Regex Patters
    split_by_version = r'-\d+[-._]*\d*'
    namever_pattern = r'.*-\d+[-._]*\d*'

    # Formatted Ohsnap Data
    ohsnp_rpm_names = [re.split(split_by_version, rpm)[0] for rpm in ohsnap_rpms]
    ohsnap_rpm_name_vers = [re.findall(namever_pattern, rpm)[0] for rpm in ohsnap_rpms]

    # Comparing installed rpms with ohsnap data
    mismatch_versions = []
    for rpm in installed_rpms:
        installed_rpm_name = re.split(split_by_version, rpm)[0]
        if installed_rpm_name in ohsnp_rpm_names:
            installed_rpm_name_ver = re.findall(namever_pattern, rpm)[0]
            if installed_rpm_name_ver not in ohsnap_rpm_name_vers:
                mismatch_versions.append(rpm)

    if mismatch_versions:
        pytest.fail(f'Some RPMs are found with mismatch versions. They are {mismatch_versions}')
    assert not mismatch_versions


def test_all_interfaces_are_accessible(target_sat):
    """API, CLI and UI interfaces are accessible

    :id: 0a212120-8e49-4489-a1a4-4272004e16dc

    :expectedresults: All three satellite interfaces are accessible
    """
    errors = {}
    # API Interface
    try:
        api_org = target_sat.api.Organization(id=1).read()
        assert api_org
        assert api_org.name == 'Default Organization'
    except Exception as api_exc:
        errors['api'] = api_exc

    # CLI Interface
    try:
        cli_org = target_sat.cli.Org.info({'id': 1})
        assert cli_org
        assert cli_org['name'] == 'Default Organization'
    except Exception as cli_exc:
        errors['cli'] = cli_exc

    # UI Interface
    try:
        with target_sat.ui_session() as session:
            ui_org = session.organization.read('Default Organization', widget_names='primary')
            assert ui_org
            assert ui_org['primary']['name'] == 'Default Organization'
    except Exception as ui_exc:
        errors['ui'] = ui_exc

    # Final Exception
    if errors:
        pytest.fail(
            '\n'.join(
                [
                    f'Interface {interface} interaction failed with error {err}'
                    for interface, err in errors.items()
                ]
            )
        )
    assert True
