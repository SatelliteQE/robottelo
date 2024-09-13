# Methods related to issue handlers in general
from robottelo.utils.issue_handlers import jira


def add_workaround(data, matches, usage, validation=(lambda *a, **k: True), **kwargs):
    """Adds entry for workaround usage."""
    for match in matches:
        issue = f"{match[0]}:{match[1]}"
        if validation(data, issue, usage, **kwargs):
            data[issue.strip()]['used_in'].append({'usage': usage, **kwargs})


def should_deselect(issue, data=None):
    """Check if test should be deselected based on marked issue."""
    return jira.should_deselect_jira(issue.strip(), data)


def is_open(issue, data=None):
    """Check if specific Jira issue is open.

    Arguments:
        issue {str} -- A string containing Jira issue id e.g: SAT-12345
        data {dict} -- Issue data indexed by issue id or None
    """
    return jira.is_open_jira(issue.strip(), data)
