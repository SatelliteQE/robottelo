"""Test for Report Templates

:Requirement: Reports

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: Reporting

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import csv
import os

from nailgun import entities

from robottelo.datafactory import gen_string
from robottelo.decorators import fixture
from robottelo.decorators import stubbed
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.ui.utils import create_fake_host


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@tier3
@stubbed()
def test_negative_create_report_without_name(session):
    """ A report template with empty name can't be created

    :id: 916ec1f8-c42c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights

    :steps:

        1. Monitor -> Report Templates -> Create Template
        2. Insert any content but empty name
        3. Submit

    :expectedresults: A report should not be created and a warning should be displayed

    :CaseImportance: Medium
    """


@tier3
@stubbed()
def test_negative_cannot_delete_locked_report(session):
    """ Edit a report template

    :id: cd19b90d-830f-4efd-8cbc-d5e09a909a67

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions Column, try to click Delete

    :expectedresults: A report should not be deleted and the button should not even be clickable

    :CaseImportance: Medium
    """


@tier3
@stubbed()
def test_positive_preview_report(session):
    """ Preview a report

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


@tier2
def test_positive_end_to_end(session, module_org, module_loc):
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
    template_input = [{
        'name': input_name,
        'required': True,
        'input_type': 'User input',
        'input_content.description': gen_string('alpha')
    }]
    with session:
        # CREATE report template
        session.reporttemplate.create({
            'template.name': name,
            'template.default': True,
            'template.template_editor.editor': content,
            'template.audit_comment': gen_string('alpha'),
            'inputs': template_input,
            'type.snippet': False,
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        # READ report template
        rt = session.reporttemplate.read(name)
        assert rt['template']['name'] == name
        assert rt['template']['default'] is True
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == template_input[0]['name']
        assert rt['inputs'][0]['required'] is template_input[0]['required']
        assert rt['inputs'][0]['input_type'] == template_input[0]['input_type']
        assert rt['inputs'][0]['input_content']['description'] == \
            template_input[0]['input_content.description']
        assert rt['type']['snippet'] is False
        assert rt['locations']['resources']['assigned'][0] == module_loc.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # UPDATE report template
        session.reporttemplate.update(
            name,
            {'template.name': new_name, 'type.snippet': True}
        )
        rt = session.reporttemplate.read(new_name)
        assert rt['template']['name'] == new_name
        assert rt['type']['snippet'] is True
        # LOCK
        session.reporttemplate.lock(new_name)
        assert session.reporttemplate.is_locked(new_name) is True
        # UNLOCK
        session.reporttemplate.unlock(new_name)
        assert session.reporttemplate.is_locked(new_name) is False
        # CLONE
        session.reporttemplate.clone(
            new_name,
            {
                'template.name': clone_name,
            }
        )
        rt = session.reporttemplate.read(clone_name)
        assert rt['template']['name'] == clone_name
        assert rt['template']['default'] is True
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == input_name
        assert rt['inputs'][0]['required'] is True
        assert rt['inputs'][0]['input_type'] == 'User input'
        assert rt['type']['snippet'] is True
        assert rt['locations']['resources']['assigned'][0] == module_loc.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # EXPORT
        file_path = session.reporttemplate.export(new_name)
        assert os.path.isfile(file_path)
        with open(file_path) as dfile:
            assert content in dfile.read()
        # DELETE report template
        session.reporttemplate.delete(new_name)
        assert not session.reporttemplate.search(new_name)


@upgrade
@tier2
def test_positive_generate_registered_hosts_report(session, module_org, module_loc):
    """Use provided Registered Hosts report for testing

    :id: b44d4cd8-a78e-47cf-9993-0bb871ac2c96

    :expectedresults: The Registered Hosts report is generated (with host filter) and it
                      contains created host with correct data

    :CaseLevel: Integration

    :CaseImportance: High
    """
    # generate Host Status report
    os_name = 'comma,' + gen_string('alpha')
    os = entities.OperatingSystem(name=os_name).create()
    host_cnt = 3
    host_templates = [entities.Host(organization=module_org,
                                    location=module_loc,
                                    operatingsystem=os) for i in range(host_cnt)]
    for host_template in host_templates:
        host_template.create_missing()
    with session:
        # create multiple hosts to test filtering
        host_names = [create_fake_host(session, host_template) for host_template in host_templates]
        host_name = host_names[1]  # pick some that is not first and is not last
        file_path = session.reporttemplate.generate("Registered hosts",
                                                    values={'inputs': {'Hosts filter': host_name}})
        with open(file_path) as csvfile:
            dreader = csv.DictReader(csvfile)
            res = next(dreader)
            assert list(res.keys()) == ['Name', 'Ip', 'Operating System',
                                        'Subscriptions', 'Applicable Errata', 'Owner',
                                        'Kernel', 'Latest kernel available']
            assert res['Name'] == host_name
            # also tests comma in field contents
            assert res['Operating System'] == '{0} {1}'.format(os_name, os.major)


@tier3
@stubbed()
def test_positive_applied_errata(session):
    """ Generate an Applied Errata report

    :id: cd19b90d-836f-4efd-ccbc-d5e09a909a67
    :setup: User with reporting access rights, some host with applied errata
    :steps:
        1. Monitor -> Report Templates
        2. Applied Errata -> Generate
        3. Submit
    :expectedresults: A report is generated with all applied errata listed
    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_datetime_picker(session):
    """ Generate an Applied Errata report with date filled

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


@tier3
@stubbed()
def test_positive_autocomplete(session):
    """ Check if host field suggests matching hosts on typing

    :id: cd19b90d-836f-4efd-c2bc-d5e09a909a67
    :setup: User with reporting access rights, some Host, some report with host input
    :steps:
        1. Monitor -> Report Templates
        2. Registered Hosts -> Generate
        3. Fill in part of the Host name
        4. Check if the Host is within suggestions
        5. Select the Host
        6. Submit
    :expectedresults: The same report is generated as if the host has been entered manually
    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_positive_schedule_generation_and_get_mail(session):
    """ Schedule generating a report. Request the result be sent via e-mail.

    :id: cd19b90d-836f-4efd-c3bc-d5e09a909a67
    :setup: User with reporting access rights, some Host
    :steps:
        1. Monitor -> Report Templates
        2. Registered Hosts -> Generate
        3. Set schedule to current time + 1 minute
        4. Check that the result should be sent via e-mail
        5. Submit
        6. Receive the e-mail
    :expectedresults: After ~1 minute, the same report is generated as if
                      the results were downloaded from WebUI.
                      The result is compressed.
    :CaseImportance: High
    """


@tier3
@stubbed()
def test_negative_bad_email(session):
    """ Generate a report and request the result be sent to
        a wrong formatted e-mail address

    :id: cd19b90d-836f-4efd-c4bc-d5e09a909a67
    :setup: User with reporting access rights, some Host, some report with host input
    :steps:
        1. Monitor -> Report Templates
        2. Registered Hosts -> Generate
        3. Check that the result should be sent via e-mail
        4. Submit
    :expectedresults: Error message about wrong e-mail address, no task is triggered
    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_negative_nonauthor_of_report_cant_download_it(session):
    """ The resulting report should only be downloadable by
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
