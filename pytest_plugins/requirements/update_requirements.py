"""Plugin enables pytest to notify and update the requirements"""

from .req_updater import ReqUpdater

updater = ReqUpdater()


def git_deviation_filter(deviation):
    """Packages installed from Git branch and the version can't be compared, so ignore them from reporting"""
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
    filtered_req_deviations = list(filter(git_deviation_filter, req_deviations))
    if filtered_req_deviations:
        print(f"Mandatory Requirements Mismatch: {' '.join(filtered_req_deviations)}")
    else:
        print('Mandatory Requirements are up to date.')
    if req_deviations and (
        config.getoption('update_required_reqs') or config.getoption('update_all_reqs')
    ):
        updater.install_req_deviations()

    opt_deviations = updater.opt_deviation
    filtered_opt_deviations = list(filter(git_deviation_filter, opt_deviations))
    if filtered_opt_deviations:
        print(f"Optional Requirements Mismatch: {' '.join(filtered_opt_deviations)}")
    else:
        print('Optional Requirements are up to date.')
    if opt_deviations and config.getoption('update_all_reqs'):
        updater.install_opt_deviations()

    if req_deviations or opt_deviations:
        print(
            "To update requirements, run the pytest with "
            "'--update-required-reqs' OR '--update-all-reqs' option."
        )
