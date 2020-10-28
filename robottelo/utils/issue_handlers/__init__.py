# Methods related to issue handlers in general
from robottelo.utils.issue_handlers import bugzilla


handler_methods = {'BZ': bugzilla.is_open_bz}
SUPPORTED_HANDLERS = tuple(f"{handler}:" for handler in handler_methods.keys())


def add_workaround(data, matches, usage, validation=(lambda *a, **k: True), **kwargs):
    """Adds entry for workaround usage."""
    for match in matches:
        issue = f"{match[0]}:{match[1]}"
        if validation(data, issue, usage, **kwargs):
            data[issue.strip()]['used_in'].append({'usage': usage, **kwargs})


def should_deselect(issue, data=None):
    """Check if test should be deselected based on marked issue."""
    # Handlers can be extended to support different issue trackers.
    handlers = {'BZ': bugzilla.should_deselect_bz}
    supported_handlers = tuple(f"{handler}:" for handler in handlers.keys())
    if str(issue).startswith(supported_handlers):
        handler_code = str(issue).partition(":")[0]
        return handlers[handler_code.strip()](issue.strip(), data)


def is_open(issue, data=None):
    """Check if specific issue is open.

    Issue must be prefixed by its handler e.g:

    Bugzilla: BZ:123456

    Arguments:
        issue {str} -- A string containing handler + number e.g: BZ:123465
        data {dict} -- Issue data indexed by <handler>:<number> or None
    """
    # Handlers can be extended to support different issue trackers.
    if str(issue).startswith(SUPPORTED_HANDLERS):
        handler_code = str(issue).partition(":")[0]
    else:  # EAFP
        raise AttributeError(
            "is_open argument must be a string starting with a handler code "
            "e.g: 'BZ:123456'"
            f"supported handlers are: {SUPPORTED_HANDLERS}"
        )
    return handler_methods[handler_code.strip()](issue.strip(), data)
