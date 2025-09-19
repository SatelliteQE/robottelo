from functools import cached_property
import subprocess
import sys


class UsageError(Exception):
    """The UsageError raised when the package manager is different from uv or pip"""

    pass


class ReqUpdater:
    # Installed package name as key and its counterpart in requirements file as value
    package_deviates = {
        'broker': 'broker[docker,podman,hussh]',
        'dynaconf': 'dynaconf[vault]',
        'Jinja2': 'jinja2',
        'Sphinx': 'sphinx',
        'pyyaml': 'PyYAML',
    }

    @cached_property
    def installed_packages(self):
        """Returns the list of installed packages in venv

        This also normalizes any package names that deviates in requirements file vs installed names
        """
        installer_args = [sys.executable, '-m', 'list', '--format=freeze']
        installer_args[2:2] = self.packagae_manager.split(' ')
        installed_pkges = subprocess.run(installer_args, capture_output=True).stdout.decode()
        for pkg in self.package_deviates:
            if pkg in installed_pkges:
                # Replacing the installed package names with their names in requirements file
                installed_pkges = installed_pkges.replace(pkg, self.package_deviates[pkg])
        return installed_pkges.splitlines()

    def package_filter(self, package):
        """Filter for eliminating lines which are not requirements from files"""
        discard_list = ('#', 'git', '--')
        return not package.startswith(discard_list)

    @cached_property
    def requirements_packages(self):
        """Returns list of requirements from requirements file"""
        with open('requirements.txt') as reqf:
            req_packages = [line.strip() for line in reqf.readlines() if line.strip()]
        return list(filter(self.package_filter, req_packages))

    @cached_property
    def optional_packages(self):
        """Returns list of requirements from requirements-optional file"""
        with open('requirements-optional.txt') as reqo:
            opt_packages = [line.strip() for line in reqo.readlines() if line.strip()]
        return list(filter(self.package_filter, opt_packages))

    @cached_property
    def req_deviation(self):
        """Returns new and updates available packages in requirements file"""
        return set(self.requirements_packages).difference(self.installed_packages)

    @cached_property
    def opt_deviation(self):
        """Returns new and updates available packages in requirements-optional file"""
        return set(self.optional_packages).difference(self.installed_packages)

    @cached_property
    def packagae_manager(self):
        if (
            subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        ):
            _manager = 'pip'
        elif (
            subprocess.run(
                [sys.executable, '-m', 'uv', '--version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        ):
            _manager = 'uv pip'
        else:
            raise UsageError(
                'The package manager is not identifiable for performing package updates.'
                'Currently only pip and uv is supported. Please manually update the packages '
                'and rerun pytest command.'
            )
        return _manager

    def install_req_deviations(self):
        """Installs new and updates available packages in requirements file"""
        if self.req_deviation:
            lst_of_reqs = ' '.join(f"'{req}'" for req in self.req_deviation)
            if (
                subprocess.run(
                    f"{self.packagae_manager} install {lst_of_reqs}",
                    shell=True,
                    stdout=subprocess.PIPE,
                ).returncode
                == 0
            ):
                print('Mandatory requirements are updated.')
            else:
                print('ERROR: Some issue occurred with updating the required requirements')

    def install_opt_deviations(self):
        """Installs new and updates available packages in requirements-optional file"""
        if self.opt_deviation:
            lst_of_reqs = ' '.join(f"'{req}'" for req in self.opt_deviation)
            if (
                subprocess.run(
                    f"{self.packagae_manager} install {lst_of_reqs}",
                    shell=True,
                    stdout=subprocess.PIPE,
                ).returncode
                == 0
            ):
                print('Optional requirements are updated.')
            else:
                print('ERROR: Some issue occurred with updating the optional requirements')
