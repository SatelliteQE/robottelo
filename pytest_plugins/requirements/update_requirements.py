"""Plugin enables pytest to notify and update the requirements"""
from .req_updater import ReqUpdater
from robottelo.constants import Colored

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
    # pytest tests/foreman --collect-only --upgrade-required-reqs

    # Following will update the mandatory and optional requirements
    # pytest tests/foreman --collect-only --upgrade-all-reqs
    """
    if updater.req_deviation:
        print(
            f"{Colored.REDLIGHT}Mandatory Requirements Available: "
            f"{' '.join(updater.req_deviation)}{Colored.RESET}"
        )
        if config.getoption('update_required_reqs') or config.getoption('update_all_reqs'):
            print('Updating the mandatory requirements on demand ....')
            updater.install_req_deviations()

    if updater.opt_deviation:
        print(
            f"{Colored.REDLIGHT}Optional Requirements Available: "
            f"{' '.join(updater.opt_deviation)}{Colored.RESET}"
        )
        if config.getoption('update_all_reqs'):
            print('Updating the optional requirements on demand ....')
            updater.install_opt_deviations()
