import subprocess
from functools import cached_property


class ReqUpdater:

    # Installed package name as key and its counterpart in requirements file as value
    package_deviates = {
        'Betelgeuse': 'betelgeuse',
        'broker': 'broker[docker]',
        'dynaconf': 'dynaconf[vault]',
    }

    @cached_property
    def installed_packages(self):
        """Returns the list of installed packages in venv

        This also normalizes any package names that deviates in requirements file vs installed names
        """
        installed_pkges = subprocess.run(
            'pip list --format=freeze', capture_output=True, shell=True
        ).stdout.decode()
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

    def install_req_deviations(self):
        """Installs new and updates available packages in requirements file"""
        if self.req_deviation:
            subprocess.run(
                f"pip install {' '.join(self.req_deviation)}", shell=True, stdout=subprocess.PIPE
            )

    def install_opt_deviations(self):
        """Installs new and updates available packages in requirements-optional file"""
        if self.opt_deviation:
            subprocess.run(
                f"pip install {' '.join(self.opt_deviation)}", shell=True, stdout=subprocess.PIPE
            )
