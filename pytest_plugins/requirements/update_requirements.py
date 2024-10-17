"""Plugin enables pytest to notify and update the requirements"""

from .req_updater import ReqUpdater

updater = ReqUpdater()


def git_deviation_filter(deviation):
    """Packages installed from Git branch and the version cant be compared, so ignore them from reporting"""
    git_packages = ['nailgun', 'airgun']
    return all(git_pckg not in deviation for git_pckg in git_packages)


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
    req_deviations = updater.req_deviation
    if req_deviations:
        # req_deviations = ignore_git_deviations(req_deviations)
        req_deviations = list(filter(git_deviation_filter, req_deviations))
        if req_deviations:
            print(f"Mandatory Requirements Mismatch: {' '.join(req_deviations)}")
        if config.getoption('update_required_reqs') or config.getoption('update_all_reqs'):
            updater.install_req_deviations()
    else:
        print('Mandatory Requirements are up to date.')

    opt_deviations = updater.opt_deviation
    if opt_deviations:
        # opt_deviations = ignore_git_deviations(opt_deviations)
        opt_deviations = list(filter(git_deviation_filter, opt_deviations))
        if opt_deviations:
            print(f"Optional Requirements Mismatch: {' '.join(updater.opt_deviation)}")
        if config.getoption('update_all_reqs'):
            updater.install_opt_deviations()
    else:
        print('Optional Requirements are up to date.')

    if updater.req_deviation or updater.opt_deviation:
        print(
            "To update requirements, run the pytest with "
            "'--update-required-reqs' OR '--update-all-reqs' option."
        )
