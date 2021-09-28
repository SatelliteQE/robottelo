"""Test for Report Templates

:Requirement: Reports

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: Reporting

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import csv
import json
import os
from pathlib import PurePath

import pytest
import yaml
from lxml import etree
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.config import robottelo_tmp_dir
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.datafactory import gen_string
from robottelo.ui.utils import create_fake_host


@pytest.fixture(scope='module')
def setup_content(module_org):
    with manifests.clone() as manifest:
        upload_manifest(module_org.id, manifest.content)
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    custom_product = entities.Product(organization=module_org).create()
    custom_repo = entities.Repository(
        name=gen_string('alphanumeric').upper(), product=custom_product
    ).create()
    custom_repo.sync()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    cv = entities.ContentView(
        organization=module_org,
        repository=[rh_repo_id, custom_repo.id],
    ).create()
    cv.publish()
    cvv = cv.read().version[0].read()
    promote(cvv, lce.id)
    ak = entities.ActivationKey(
        content_view=cv, organization=module_org, environment=lce, auto_attach=True
    ).create()
    subscription = entities.Subscription(organization=module_org).search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    ak.add_subscriptions(data={'quantity': 1, 'subscription_id': subscription.id})
    return module_org, ak


@pytest.mark.tier3
@pytest.mark.stubbed
def test_negative_create_report_without_name(session):
    """A report template with empty name can't be created

    :id: 916ec1f8-c42c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights

    :steps:

        1. Monitor -> Report Templates -> Create Template
        2. Insert any content but empty name
        3. Submit

    :expectedresults: A report should not be created and a warning should be displayed

    :CaseImportance: Medium
    """


@pytest.mark.tier3
@pytest.mark.stubbed
def test_negative_cannot_delete_locked_report(session):
    """Edit a report template

    :id: cd19b90d-830f-4efd-8cbc-d5e09a909a67

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions Column, try to click Delete

    :expectedresults: A report should not be deleted and the button should not even be clickable

    :CaseImportance: Medium
    """


@pytest.mark.tier3
@pytest.mark.stubbed
def test_positive_preview_report(session):
    """Preview a report

    :id: cd19b90d-836f-4efd-8cbc-d5e09a909a67

    :setup: User with reporting access rights, some report template

    :steps:

        1. Monitor -> Report Templates
        2. Open the report template
        3. Go to Preview tab

    :expectedresults: A report preview should be shown, with correct but
                      limited data (load_hosts macro should only list 10 records)

    :CaseImportance: Medium
    """


@pytest.mark.tier2
def test_positive_end_to_end(session, module_org, module_location):
    """Perform end to end testing for report template component's CRUD operations

    :id: b44d4cc8-a78e-47cf-9993-0bb871ac2c96

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    content = gen_string('alpha')
    new_name = gen_string('alpha')
    clone_name = gen_string('alpha')
    input_name = gen_string('alpha')
    template_input = [
        {
            'name': input_name,
            'required': True,
            'input_type': 'User input',
            'input_content.description': gen_string('alpha'),
        }
    ]
    with session:
        # CREATE report template
        session.reporttemplate.create(
            {
                'template.name': name,
                'template.default': False,
                'template.template_editor.editor': content,
                'template.audit_comment': gen_string('alpha'),
                'inputs': template_input,
                'type.snippet': False,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        # READ report template
        rt = session.reporttemplate.read(name)
        assert rt['template']['name'] == name
        assert rt['template']['default'] is False
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == template_input[0]['name']
        assert rt['inputs'][0]['required'] is template_input[0]['required']
        assert rt['inputs'][0]['input_type'] == template_input[0]['input_type']
        assert (
            rt['inputs'][0]['input_content']['description']
            == template_input[0]['input_content.description']
        )
        assert rt['type']['snippet'] is False
        assert rt['locations']['resources']['assigned'][0] == module_location.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # UPDATE report template
        session.reporttemplate.update(name, {'template.name': new_name, 'type.snippet': True})
        rt = session.reporttemplate.read(new_name)
        assert rt['template']['name'] == new_name
        assert rt['template']['default'] is False
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == template_input[0]['name']
        assert rt['inputs'][0]['required'] is template_input[0]['required']
        assert rt['inputs'][0]['input_type'] == template_input[0]['input_type']
        assert (
            rt['inputs'][0]['input_content']['description']
            == template_input[0]['input_content.description']
        )
        assert rt['type']['snippet'] is True
        assert rt['locations']['resources']['assigned'][0] == module_location.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # LOCK
        session.reporttemplate.lock(new_name)
        assert session.reporttemplate.is_locked(new_name) is True
        # UNLOCK
        session.reporttemplate.unlock(new_name)
        assert session.reporttemplate.is_locked(new_name) is False
        # CLONE
        session.reporttemplate.clone(new_name, {'template.name': clone_name})
        rt = session.reporttemplate.read(clone_name)
        assert rt['template']['name'] == clone_name
        assert rt['template']['default'] is False
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == input_name
        assert rt['inputs'][0]['required'] is True
        assert rt['inputs'][0]['input_type'] == 'User input'
        assert rt['type']['snippet'] is True
        assert rt['locations']['resources']['assigned'][0] == module_location.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # EXPORT
        file_path = session.reporttemplate.export(new_name)
        assert os.path.isfile(file_path)
        with open(file_path) as dfile:
            assert content in dfile.read()
        # DELETE report template
        session.reporttemplate.delete(new_name)
        assert not session.reporttemplate.search(new_name)


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_generate_registered_hosts_report(session, module_org, module_location):
    """Use provided Host - Registered Content Hosts report for testing

    :id: b44d4cd8-a78e-47cf-9993-0bb871ac2c96

    :expectedresults: The Host - Registered Content Hosts report is generated (with host filter)
                      and it contains created host with correct data

    :CaseLevel: Integration

    :CaseImportance: High
    """
    # generate Host Status report
    os_name = 'comma,' + gen_string('alpha')
    os = entities.OperatingSystem(name=os_name).create()
    host_cnt = 3
    host_templates = [
        entities.Host(organization=module_org, location=module_location, operatingsystem=os)
        for i in range(host_cnt)
    ]
    for host_template in host_templates:
        host_template.create_missing()
    with session:
        # create multiple hosts to test filtering
        host_names = [create_fake_host(session, host_template) for host_template in host_templates]
        host_name = host_names[1]  # pick some that is not first and is not last
        file_path = session.reporttemplate.generate(
            'Host - Registered Content Hosts', values={'hosts_filter': host_name}
        )
        with open(file_path) as csvfile:
            dreader = csv.DictReader(csvfile)
            res = next(dreader)
            assert list(res.keys()) == [
                'Name',
                'Ip',
                'Operating System',
                'Subscriptions',
                'Applicable Errata',
                'Owner',
                'Kernel',
                'Latest kernel available',
            ]
            assert res['Name'] == host_name
            # also tests comma in field contents
            assert res['Operating System'] == f'{os_name} {os.major}'


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_generate_subscriptions_report_json(
    session, module_org, module_location, setup_content
):
    """Use provided Subscriptions report, generate JSON

    :id: b44d4cd8-a88e-47cf-9993-0bb871ac2c96

    :expectedresults: The Subscriptions report is generated in JSON

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    # generate Subscriptions report
    with session:
        file_path = session.reporttemplate.generate(
            'Subscription - General Report', values={'output_format': 'JSON'}
        )
    with open(file_path) as json_file:
        data = json.load(json_file)
    subscription_cnt = len(entities.Subscription(organization=module_org).search())
    assert subscription_cnt > 0
    assert len(data) >= subscription_cnt
    keys_expected = [
        'Account number',
        'Available',
        'Contract number',
        'End date',
        'ID',
        'Name',
        'Organization',
        'Quantity',
        'SKU',
        'Start date',
    ]
    for subscription in data:
        assert sorted(list(subscription.keys())) == keys_expected


@pytest.mark.tier3
@pytest.mark.stubbed
def test_positive_applied_errata(session):
    """Generate an Applied Errata report

    :id: cd19b90d-836f-4efd-ccbc-d5e09a909a67
    :setup: User with reporting access rights, some host with applied errata
    :steps:
        1. Monitor -> Report Templates
        2. Applied Errata -> Generate
        3. Submit
    :expectedresults: A report is generated with all applied errata listed
    :CaseImportance: Medium
    """


@pytest.mark.tier2
@pytest.mark.stubbed
def test_datetime_picker(session):
    """Generate an Applied Errata report with date filled

    :id: cd19b90d-836f-4efd-c1bc-d5e09a909a67
    :setup: User with reporting access rights, some host with applied errata at
            time A, some host (can be the same host) with applied
            errata at time B>A and no errata applied at other time
    :steps:
        1. Monitor -> Report Templates
        2. Applied Errata -> Generate
        3. Fill in timeFrom>A
        4. Fill in B>timeTo
        5. Generate
    :expectedresults: A report is generated with all applied errata listed
                      that were generated before timeFrom and timeTo
    :CaseImportance: High
    """


@pytest.mark.tier3
@pytest.mark.stubbed
def test_positive_autocomplete(session):
    """Check if host field suggests matching hosts on typing

    :id: cd19b90d-836f-4efd-c2bc-d5e09a909a67
    :setup: User with reporting access rights, some Host, some report with host input
    :steps:
        1. Monitor -> Report Templates
        2. Host - Registered Content Hosts -> Generate
        3. Fill in part of the Host name
        4. Check if the Host is within suggestions
        5. Select the Host
        6. Submit
    :expectedresults: The same report is generated as if the host has been entered manually
    :CaseImportance: Medium
    """


@pytest.mark.tier2
def test_positive_schedule_generation_and_get_mail(
    session, module_org, module_location, default_sat
):
    """Schedule generating a report. Request the result be sent via e-mail.

    :id: cd19b90d-836f-4efd-c3bc-d5e09a909a67
    :setup: User with reporting access rights, some Host
    :steps:
        1. Monitor -> Report Templates
        2. Host - Registered Content Hosts -> Generate
        3. Set schedule to current time + 1 minute
        4. Check that the result should be sent via e-mail
        5. Submit
        6. Receive the e-mail
    :expectedresults: After ~1 minute, the same report is generated as if
                      the results were downloaded from WebUI.
                      The result is compressed.
    :CaseImportance: High
    """
    # generate Subscriptions report
    with session:
        session.reporttemplate.schedule(
            'Subscription - General Report',
            values={
                'output_format': 'JSON',
                'generate_at': '1970-01-01 17:10:00',
                'email': True,
                'email_to': 'root@localhost',
            },
        )
    file_path = PurePath('/tmp/').joinpath(f'{gen_string("alpha")}.json')
    gzip_path = PurePath(f'{file_path}.gz')
    local_gzip_file = robottelo_tmp_dir.joinpath(gzip_path.name)
    expect_script = (
        f'#!/usr/bin/env expect\n'
        f'spawn mail\n'
        f'expect "& "\n'
        f'send "w $ /dev/null\\r"\n'
        f'expect "Enter filename"\n'
        f'send "\\r"\n'
        f'expect "Enter filename"\n'
        f'send "\\r"\n'
        f'expect "Enter filename"\n'
        f'send "\\025{gzip_path}\\r"\n'
        f'expect "&"\n'
        f'send "q\\r"\n'
    )

    default_sat.execute(f"expect -c '{expect_script}'")
    default_sat.get(remote_path=str(gzip_path), local_path=str(local_gzip_file))
    os.system(f'gunzip {local_gzip_file}')
    data = json.load(local_gzip_file.read_text())
    subscription_search = default_sat.api.Subscription(organization=module_org).search()
    assert len(data) >= len(subscription_search) > 0
    keys_expected = [
        'Account number',
        'Available',
        'Contract number',
        'End date',
        'ID',
        'Name',
        'Organization',
        'Quantity',
        'SKU',
        'Start date',
    ]
    for subscription in data:
        assert sorted(list(subscription.keys())) == keys_expected


@pytest.mark.tier3
@pytest.mark.stubbed
def test_negative_bad_email(session):
    """Generate a report and request the result be sent to
        a wrong formatted e-mail address

    :id: cd19b90d-836f-4efd-c4bc-d5e09a909a67
    :setup: User with reporting access rights, some Host, some report with host input
    :steps:
        1. Monitor -> Report Templates
        2. Host - Registered Content Hosts -> Generate
        3. Check that the result should be sent via e-mail
        4. Submit
    :expectedresults: Error message about wrong e-mail address, no task is triggered
    :CaseImportance: Medium
    """


@pytest.mark.tier2
@pytest.mark.stubbed
def test_negative_nonauthor_of_report_cant_download_it(session):
    """The resulting report should only be downloadable by
        the user that generated it. Check.

    :id: cd19b90d-836f-4efd-c6bc-d5e09a909a67
    :setup: Installed Satellite, user that can list running tasks
    :steps:
        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Generate
        3. Submit
        4. Wait for dynflow
        5. As a different user, try to download the generated report
    :expectedresults: Report can't be downloaded. Error.
    :CaseImportance: High
    """


@pytest.mark.tier3
def test_positive_gen_entitlements_reports_multiple_formats(
    session, setup_content, rhel7_contenthost, default_sat
):
    """Generate reports using the Entitlements template in html, yaml, json, and csv format.

    :id: b268663d-c213-4e59-8f81-61bec0838b1e


    :setup: Installed Satellite with Organization, Activation key,
            Content View, Content Host, and Subscriptions.

    :steps:
        1. Monitor -> Report Templates
        2. Entitlements -> Generate
        3. Click the dropdown to select output format
        4. Submit

    :expectedresults: reports are generated containing all the expected information
                      regarding Entitlements for each output format.

    :CaseImportance: High
    """
    client = rhel7_contenthost
    client.install_katello_ca(default_sat)
    module_org, ak = setup_content
    client.register_contenthost(module_org.label, ak.name)
    assert client.subscribed
    with session:
        session.location.select('Default Location')
        result_json = session.reporttemplate.generate(
            'Subscription - Entitlement Report', values={'output_format': 'JSON'}
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)
        assert any(entitlement['Host Name'] == client.hostname for entitlement in data_json)
        assert any(
            entitlement['Subscription Name'] == DEFAULT_SUBSCRIPTION_NAME
            for entitlement in data_json
        )
        result_yaml = session.reporttemplate.generate(
            'Subscription - Entitlement Report', values={'output_format': 'YAML'}
        )
        with open(result_yaml) as yaml_file:
            data_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)
        assert any(entitlement['Host Name'] == client.hostname for entitlement in data_yaml)
        assert any(
            entitlement['Subscription Name'] == DEFAULT_SUBSCRIPTION_NAME
            for entitlement in data_yaml
        )
        result_csv = session.reporttemplate.generate(
            'Subscription - Entitlement Report', values={'output_format': 'CSV'}
        )
        with open(result_csv) as csv_file:
            data_csv = csv.DictReader(csv_file)
            items = list(data_csv)
        assert any(entitlement['Host Name'] == client.hostname for entitlement in items)
        assert any(
            entitlement['Subscription Name'] == DEFAULT_SUBSCRIPTION_NAME for entitlement in items
        )
        result_html = session.reporttemplate.generate(
            'Subscription - Entitlement Report', values={'output_format': 'HTML'}
        )
        with open(result_html) as html_file:
            parser = etree.HTMLParser()
            tree = etree.parse(html_file, parser)
            tree_result = etree.tostring(tree.getroot(), pretty_print=True, method='html').decode()
        assert client.hostname in tree_result
        assert DEFAULT_SUBSCRIPTION_NAME in tree_result
