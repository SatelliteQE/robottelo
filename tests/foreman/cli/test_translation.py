"""Tests for verifying translation completeness on Satellite.

:CaseAutomation: Automated

:CaseComponent: LocalizationInternationalization

:team: Dragonfly

"""

import os
import re

import pytest

from robottelo.constants import SUPPORTED_LANGUAGES
from robottelo.utils.issue_handlers import is_open

LOCALE_DIRS = (
    '/usr/share/foreman/locale/',
    '/usr/share/gems/gems/{katello,foreman,hammer_cli}*/locale/',
)
FIND_POT = f"find {' '.join(LOCALE_DIRS)} -name '*.pot'"


@pytest.fixture(params=SUPPORTED_LANGUAGES)
def supported_language(request):
    return request.param


def test_positive_check_missing_translations(target_sat, supported_language):
    """Verify that all translation files have 100% translated messages
    and are complete relative to their templates.

    :id: f33c2ad0-02fd-4d50-b1a9-9b6c66a23700

    :parametrized: yes

    :Verifies: SAT-32747

    :steps:
        1. Find all .po translation files on the Satellite.
        2. Run ``msgfmt --statistics`` on each file to detect untranslated messages.
        3. For files with untranslated messages, run ``msgattrib --untranslated``
           to list them.
        4. Find all .pot template files and compare each .po file against its
           template using ``msgcmp`` to detect missing translations.

    :expectedresults:
        1. All translation files are found on the Satellite.
        2. No translation file contains untranslated messages.
        3. No translation file is missing strings defined in its template.

    :CaseImportance: Medium
    """
    # Step 1: Find all .po translation files for the given language
    po_search_dirs = ' '.join(os.path.join(dir_, supported_language, '') for dir_ in LOCALE_DIRS)
    find_po = f"find {po_search_dirs} -name '*.po'"
    result = target_sat.execute(find_po)
    assert result.status == 0, f'Failed to search for .po files: {result.stderr}'
    po_files = result.stdout.strip().splitlines()
    assert po_files, 'No .po translation files found on the Satellite'

    # Step 2 & 3: Check each .po file for untranslated messages
    untranslated_report = {}
    for po_file in po_files:
        stats = target_sat.execute(f'msgfmt -v --statistics -o /dev/null {po_file}')
        if 'untranslated' in stats.stderr:
            details = target_sat.execute(f'msgattrib --untranslated --indent --no-wrap {po_file}')
            untranslated_report[po_file] = {
                'statistics': stats.stderr.strip(),
                'messages': '\n'.join(
                    [line for line in details.stdout.splitlines() if not line.startswith('#')]
                ),
            }

    # Step 4: Compare .po files against their .pot templates
    result = target_sat.execute(FIND_POT)
    assert result.status == 0, f'Failed to search for .pot files: {result.stderr}'
    pot_files = result.stdout.strip().splitlines()

    template_failures = {}
    for pot_file in pot_files:
        locale_dir = os.path.dirname(pot_file)
        pot_name = os.path.splitext(os.path.basename(pot_file))[0]

        related_pos = [po for po in po_files if po.startswith(locale_dir) and pot_name in po]
        for po_file in related_pos:
            cmp_result = target_sat.execute(f'msgcmp {po_file} {pot_file}')
            not_defined = []
            for line in cmp_result.stderr.splitlines():
                if f'not defined in {po_file}' in line:
                    match = re.search(r':(\d+):', line)
                    line_number = int(match.group(1)) if match else 0
                    pot_line = ''
                    if line_number:
                        get_line_result = target_sat.execute(
                            f"sed -n '{line_number - 1}p' {pot_file}"
                        )
                        pot_line = get_line_result.stdout.strip()
                    not_defined.append((pot_line, line.strip()))
            if not_defined:
                template_failures[po_file] = not_defined

    errors = []
    if untranslated_report:
        summary = '\n'.join(
            f"{info['statistics']}\n{info['messages']}\n" for info in untranslated_report.values()
        )
        errors.append(f'Files with untranslated messages:\n{summary}')
    if template_failures:
        lines = []
        for po_file, entries in template_failures.items():
            lines.append(f'{po_file}:')
            for pot_line, msg in entries:
                lines.append(f'  {msg}\n    {pot_line}')
        errors.append('Files with missing translations relative to template:\n' + '\n'.join(lines))

    # This code block can be removed once all translation issues are resolved.
    open_issues = {'fr': 'SAT-48297', 'ja': 'SAT-48299', 'ko': 'SAT-48300', 'zh_CN': 'SAT-48301'}
    if errors and open_issues.get(supported_language) and is_open(open_issues[supported_language]):
        pytest.xfail(
            f'Translation of language {supported_language} is still in progress ({open_issues[supported_language]}).\n'
            'Missing translations:\n' + '\n\n'.join(errors)
        )

    assert not errors, '\n\n'.join(errors)
