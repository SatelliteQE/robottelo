"""Plugin enables pytest to notify and update the requirements"""

from .req_updater import ReqUpdater

updater = ReqUpdater()


def pytest_addoption(parser):
    """Options to allow user to update the requirements"""
    update_options = {
        '--update-required-reqs': 'Install mandatory requirements from requirements.txt',
        '--update-all-reqs': 'Install optional requirements from requirements-optional.txt',
    }
    for opt, help_text in update_options.items():
        parser.addoption(opt, action='store_true', default=False, help=help_text)


def pytest_report_header(config):
    """
    Adds a suggestion of requirements updates in to the Pytest Report Header

    It also updates the requirements if pytest options are provided,
    e.g:

    # Following will update the mandatory requirements
    # pytest tests/foreman --collect-only --update-required-reqs

    # Following will update the mandatory and optional requirements
    # pytest tests/foreman --collect-only --update-all-reqs
    """
    if updater.req_deviation:
        print(f"Mandatory Requirements Mismatch: {' '.join(updater.req_deviation)}")
        if config.getoption('update_required_reqs') or config.getoption('update_all_reqs'):
            updater.install_req_deviations()
            print('Mandatory requirements are installed to be up-to-date.')
    else:
        print('Mandatory Requirements are up to date.')

    if updater.opt_deviation:
        print(f"Optional Requirements Mismatch: {' '.join(updater.opt_deviation)}")
        if config.getoption('update_all_reqs'):
            updater.install_opt_deviations()
            print('Optional requirements are installed to be up-to-date.')
    else:
        print('Optional Requirements are up to date.')

    if updater.req_deviation or updater.opt_deviation:
        print(
            "To update mismatched requirements, run the pytest command with "
            "'--update-required-reqs' OR '--update-all-reqs' option."
        )
