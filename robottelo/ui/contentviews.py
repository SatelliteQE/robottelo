# -*- encoding: utf-8 -*-
"""Implements Content Views UI"""

import time

from robottelo.constants import FILTER_ERRATA_DATE, FILTER_ERRATA_TYPE
from robottelo.decorators import bz_bug_is_open
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class ContentViews(Base):
    """Manipulates Content Views from UI"""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Content Views entity page"""
        Navigator(self.browser).go_to_content_views()

    def _search_locator(self):
        """Specify locator for Content Views entity search procedure"""
        return locators["contentviews.key_name"]

    def go_to_filter_page(self, cv_name, filter_name):
        """Navigates UI to selected Filter page"""
        self.search_and_click(cv_name)
        self.click(tab_locators['contentviews.tab_yum_content'])
        self.click(locators['contentviews.content_filters'])
        self.assign_value(
            locators['contentviews.search_filters'], filter_name)
        self.click(common_locators['kt_search_button'])
        self.click(locators['contentviews.select_filter_name'] % filter_name)

    def set_calendar_date_value(self, name, value):
        """Set the input value of a date field and press the button to hide
         the calendar popup panel"""
        self.assign_value(
            locators.contentviews.calendar_date_input % name,
            value
        )
        # the calendar panel popup and hide other form elements that became
        # unreachable.
        # close the popup calendar panel
        button = self.wait_until_element(
            locators.contentviews.calendar_date_button % name, timeout=2)
        if button:
            self.click(button)

    def create(self, name, label=None, description=None, is_composite=False):
        """Creates a content view"""
        self.click(locators['contentviews.new'])
        self.assign_value(common_locators['name'], name)
        timeout = 60 if len(name) > 50 else 30
        self.wait_for_ajax(timeout)
        if label is not None:
            self.assign_value(common_locators['label'], label)
        if description is not None:
            self.assign_value(common_locators['description'], description)
        if is_composite:
            self.click(locators['contentviews.composite'])
        self.click(common_locators['create'])

    def move_affected_components(self, env, cv):
        """Move affected components to another environment or content view.
        Activation keys and content hosts are examples of affected components.
        """
        self.click(locators['contentviews.change_env'] % env)
        self.select(locators['contentviews.change_cv'], cv)
        self.click(locators['contentviews.next_button'])

    def delete_version(self, name, version):
        """Deletes published content view's version"""
        self.search_and_click(name)
        self.click(locators['contentviews.version_dropdown'] % version)
        self.click(locators['contentviews.remove_ver'] % version)
        self.assign_value(
            locators['contentviews.completely_remove_checkbox'], True)
        self.click(locators['contentviews.next_button'])
        self.click(locators['contentviews.confirm_remove_ver'])

    def search_filter(self, cv_name, filter_name):
        """Uses search box to locate the filters"""
        self.search_and_click(cv_name)
        self.click(tab_locators['contentviews.tab_yum_content'])
        self.click(locators['contentviews.content_filters'])
        self.assign_value(
            locators['contentviews.search_filters'], filter_name)
        self.click(common_locators['kt_search_button'])
        return self.wait_until_element(
            locators['contentviews.filter_name'] % filter_name)

    def update(self, name, new_name=None, new_description=None,
               force_puppet=None):
        """Updates an existing content view"""
        self.search_and_click(name)
        self.click(tab_locators['contentviews.tab_details'])
        if new_name:
            self.edit_entity(
                locators['contentviews.edit_name'],
                locators['contentviews.edit_name_text'],
                new_name,
                locators['contentviews.save_name'],
            )
        if new_description:
            self.edit_entity(
                locators['contentviews.edit_description'],
                locators['contentviews.edit_description_text'],
                new_description,
                locators['contentviews.save_description']
            )
        if force_puppet is not None:
            self.edit_entity(
                locators['contentviews.edit_force_puppet'],
                locators['contentviews.edit_force_puppet_checkbox'],
                force_puppet,
                locators['contentviews.save_force_puppet']
            )

    def add_remove_repos(
            self, cv_name, repo_names, add_repo=True, repo_type='yum'):
        """Add or Remove repository to/from selected content-view.

        When 'add_repo' Flag is set then add_repository will be performed,
        otherwise remove_repository
        """
        self.search_and_click(cv_name)
        if repo_type == 'yum':
            self.click(tab_locators['contentviews.tab_yum_content'])
            self.click(locators['contentviews.content_repo'])
        elif repo_type == 'docker':
            self.click(tab_locators['contentviews.tab_docker_content'])
            self.click(locators['contentviews.docker_repo'])
        elif repo_type == 'ostree':
            self.click(tab_locators['contentviews.tab_ostree_content'])
        locator = locators['contentviews.select_repo']
        for repo_name in repo_names:
            if add_repo:
                self.click(tab_locators['contentviews.tab_repo_add'])
            else:
                self.click(tab_locators['contentviews.tab_repo_remove'])
            self.assign_value(
                locators['contentviews.repo_search'], repo_name)
            self.click(common_locators['kt_search_button'])
            if not self.wait_until_element(locator % repo_name):
                raise UIError(
                    'Could not find repo "{0}" to add into CV'
                    .format(repo_name)
                )
            self.click(locator % repo_name)
            if add_repo:
                self.click(locators['contentviews.add_repo'])
                self.click(tab_locators['contentviews.tab_repo_remove'])
                element = self.wait_until_element(locator % repo_name)
                if element is None:
                    raise UINoSuchElementError(
                        "Adding repo {0} failed".format(repo_name))
            else:
                self.click(locators['contentviews.remove_repo'])
                self.click(tab_locators['contentviews.tab_repo_add'])
                element = self.wait_until_element(locator % repo_name)
                if element is None:
                    raise UINoSuchElementError(
                        "Removing repo {0} fails".format(repo_name))

    def check_progress_bar_status(self, version):
        """Checks the status of progress bar while publishing and promoting the
        CV to next environment
        """
        timer = time.time() + 60 * 10
        strategy, value = locators['contentviews.publish_progress']
        check_progress = self.wait_until_element(
            (strategy, value % version),
            timeout=12,
            poll_frequency=2,
        )
        while check_progress and time.time() <= timer:
            check_progress = self.wait_until_element(
                (strategy, value % version),
                timeout=1,
                poll_frequency=0.5,
            )

    def publish(self, cv_name, description=None):
        """Publishes to create new version of CV and promotes the contents to
        'Library' environment
        """
        self.search_and_click(cv_name)
        self.click(locators['contentviews.publish'])
        version_label = self.wait_until_element(
            locators['contentviews.ver_label'])
        version_number = self.wait_until_element(
            locators['contentviews.ver_num'])
        # To fetch the publish version e.g. 'Version 1'
        version = '{0} {1}'.format(version_label.text, version_number.text)
        if description:
            self.assign_value(
                locators['contentviews.publish_description'], description)
        self.click(common_locators['create'])
        self.check_progress_bar_status(version)
        return version

    def promote(self, cv_name, version, env):
        """Promotes the selected version of content-view to given environment.
        """
        self.search_and_click(cv_name)
        self.click(tab_locators['contentviews.tab_versions'])
        self.click(locators['contentviews.promote_button'] % version)
        self.click(locators['contentviews.env_to_promote'] % env)
        self.click(locators['contentviews.promote_version'])
        self.check_progress_bar_status(version)

    def add_puppet_module(self, cv_name, module_name, filter_term):
        """Add puppet module to selected view either by its author name or by
        its version.

        Filter_term can be used to filter the module by 'author'
        or by 'version'.
        """
        self.search_and_click(cv_name)
        if self.wait_until_element(
                tab_locators['contentviews.tab_puppet_modules']):
            self.click(tab_locators['contentviews.tab_puppet_modules'])
        else:
            raise UIError('Could not find tab to add puppet_modules')
        self.click(locators['contentviews.add_module'])
        self.assign_value(
            locators['contentviews.search_filters'], module_name)
        self.click(common_locators['kt_search_button'])
        self.click(locators['contentviews.select_module'] % module_name)
        self.assign_value(
            common_locators['kt_search'], filter_term)
        self.click(locators['contentviews.select_module_ver'] % filter_term)

    def add_remove_cv(self, composite_cv, cv_names, is_add=True):
        """Add or Remove content-views to/from selected composite view.
        When 'is_add' Flag is set then add_contentView will be performed,
        otherwise remove_contentView
        """
        self.search_and_click(composite_cv)
        if self.wait_until_element(
                tab_locators['contentviews.tab_content_views']):
            self.click(tab_locators['contentviews.tab_content_views'])
        else:
            raise UINoSuchElementError(
                'Could not find ContentView tab, please make sure '
                'selected view is composite'
            )
        for cv_name in cv_names:
            if is_add:
                self.click(tab_locators['contentviews.tab_cv_add'])
            else:
                self.click(tab_locators['contentviews.tab_cv_remove'])
            locator = locators['contentviews.select_cv']
            self.click(locator % cv_name)
            if is_add:
                self.click(locators['contentviews.add_cv'])
                self.click(tab_locators['contentviews.tab_cv_remove'])
                element = self.wait_until_element(locator % cv_name)
                if element is None:
                    raise UINoSuchElementError(
                        "Adding CV {0} failed".format(cv_name))
            else:
                self.click(locators['contentviews.remove_cv'])
                self.click(tab_locators['contentviews.tab_cv_add'])
                element = self.wait_until_element(locator % cv_name)
                if element is None:
                    raise UINoSuchElementError(
                        "Removing CV {0} fails".format(cv_name))

    def add_filter(self, cv_name, filter_name,
                   content_type, filter_type, description=None):
        """Creates content-view filter of given 'type'(include/exclude) and
        'content-type'(package/package-group/errata)
        """
        self.search_and_click(cv_name)
        self.click(tab_locators['contentviews.tab_yum_content'])
        self.click(locators['contentviews.content_filters'])
        self.click(locators['contentviews.new_filter'])
        self.assign_value(common_locators['name'], filter_name)
        if content_type:
            self.select(locators['contentviews.content_type'], content_type)
        else:
            raise UIError(
                'Could not create filter without content type'
            )
        if filter_type:
            self.select(locators['contentviews.type'], filter_type)
        else:
            raise UIError(
                'Could not create filter without specifying filter '
                'type'
            )
        if description:
            self.assign_value(common_locators['description'], description)
        self.click(common_locators['create'])

    def remove_filter(self, cv_name, filter_names):
        """Removes selected filter from selected content-view."""
        self.search_and_click(cv_name)
        self.click(tab_locators['contentviews.tab_yum_content'])
        self.click(locators['contentviews.content_filters'])

        # Workaround to remove previously used search string
        # from search box
        self.find_element(locators['contentviews.search_filters']).clear()
        self.click(common_locators['kt_search_button'])
        for filter_name in filter_names:
            self.click(
                locators['contentviews.select_filter_checkbox'] % filter_name)
        self.click(locators['contentviews.remove_filter'])

    def select_package_version_value(
            self, version_type, value1=None, value2=None):
        """Select package version and set values: versions are: 'All'  'Equal
        To' 'Greater Than' 'Less Than' 'Range'.

        'value1' should contain version value for types: 'Equal To' 'Greater
        Than' 'Less Than'.

        'value2' should only be used with type 'Range' to define range of
        versions.
        """
        if version_type == 'Equal To':
            self.assign_value(
                locators['contentviews.equal_value'], value1)
        elif version_type == 'Greater Than':
            self.assign_value(
                locators['contentviews.greater_min_value'], value1)
        elif version_type == 'Less Than':
            self.assign_value(
                locators['contentviews.less_max_value'], value1)
        elif version_type == 'Range':
            self.assign_value(
                locators['contentviews.greater_min_value'], value1)
            self.assign_value(
                locators['contentviews.less_max_value'], value2)
        else:
            raise UIError('Could not find valid version type')

    def add_packages_to_filter(self, cv_name, filter_name, package_names,
                               version_types, values=None, max_values=None):
        """Adds packages to selected filter for inclusion/Exclusion"""
        self.go_to_filter_page(cv_name, filter_name)
        for package_name, version_type, value, max_value in zip(
                package_names, version_types, values, max_values):
            self.click(locators['contentviews.add_rule'])
            self.assign_value(
                locators['contentviews.input_pkg_name'], package_name)
            self.select(
                locators['contentviews.select_pkg_version'], version_type)
            if not version_type == 'All Versions':
                self.select_package_version_value(
                    version_type, value, max_value)
            self.click(locators['contentviews.add_pkg_button'])

    def remove_packages_from_filter(self, cv_name, filter_name, package_names):
        """Removes selected packages from selected package type filter."""
        self.go_to_filter_page(cv_name, filter_name)
        # On UI there's no attribute or text containing package name, just
        # disabled input with value set to package name after page loading (so
        # there's no @value attribute). This makes impossible to form xpath for
        # specific package and the only remaining option is to locate all the
        # packages and select only the one whose input contains desired value
        packages = self.find_elements(locators['contentviews.packages'])
        checkboxes = [
            package.find_element(*locators['contentviews.package_checkbox'])
            for package in packages
            if package.get_attribute('value') in package_names
        ]
        for checkbox in checkboxes:
            self.click(checkbox)
        self.click(locators['contentviews.remove_packages'])

    def update_package_filter(self, cv_name, filter_name, package_name,
                              version_type=None, version_value=None,
                              new_package_name=None, new_version_type=None,
                              new_version_value=None):
        """Update package in a filter"""
        version_types = {
            'Equal To': 'equal',
            'Greater Than': 'greater',
            'Less Than': 'less',
            'Range': 'range',
            'All Versions': 'all',
        }
        self.go_to_filter_page(cv_name, filter_name)
        # As it's impossible to obtain specific filter directly,
        # getting all the package filters first
        packages = self.find_elements(locators['contentviews.packages'])
        # Then selecting the filters with the same package as passed
        packages = [
            package for package in packages
            if package.get_attribute('value') == package_name
        ]
        # As there can be multiple filters for the same package, user may want
        # to specify version type and version of package filter
        # If version type was passed - filter package list by version type
        if version_type:
            packages = [
                package for package in packages
                if package.find_element(
                    *locators['contentviews.package_version_type']
                ).get_attribute('value') == version_types[version_type]
            ]
        # If version was passed - filter package list by version
        if version_value:
            packages = [
                package for package in packages
                if package.find_element(
                    *locators['contentviews.package_version_value']
                ).get_attribute('value') == version_value
            ]
        # What's left in package list is probably our package, let's work with
        # it
        if packages:
            package = packages[0]
        # But if package list is empty - notify user he specified something
        # wrong
        else:
            raise UINoSuchElementError('Package filter not found')
        # Now just usual stuff - clicking 'edit' button, updating corresponding
        # fields and clicking 'save' button
        self.click(
            package.find_element(*locators['contentviews.package_edit']))
        if new_package_name:
            self.assign_value(package, new_package_name)
        if new_version_type:
            self.assign_value(
                package.find_element(
                    *locators['contentviews.package_version_type']),
                new_version_type
            )
        if new_version_value:
            self.assign_value(
                package.find_element(
                    *locators['contentviews.package_version_value']),
                new_version_value
            )
        self.click(
            package.find_element(*locators['contentviews.package_save']))

    def update_filter_affected_repos(self, cv_name, filter_name,
                                     new_affected_repos):
        """Update affected repos of content view filter"""
        self.go_to_filter_page(cv_name, filter_name)
        self.click(tab_locators['contentviews.tab_filter_affected_repos'])
        self.assign_value(
            locators['contentviews.affected_repos_radio'], True)
        all_repo_checkboxes = self.find_elements(
            locators['contentviews.affected_repos_checkboxes'])
        # Uncheck all the repos first
        for checkbox in all_repo_checkboxes:
            self.assign_value(checkbox, False)
        # Check off passed repos
        for repo_name in new_affected_repos:
            self.assign_value(
                locators['contentviews.affected_repo_checkbox'] % repo_name,
                True
            )
        self.click(locators['contentviews.filter_update_repos'])

    def add_remove_package_groups_to_filter(self, cv_name, filter_name,
                                            package_groups, is_add=True):
        """Add/Remove package groups to/from selected filter for
        inclusion/Exclusion.
        """
        self.go_to_filter_page(cv_name, filter_name)
        if is_add:
            self.click(tab_locators['contentviews.tab_pkg_group_add'])
        else:
            self.click(tab_locators['contentviews.tab_pkg_group_remove'])
        for package_group in package_groups:
            self.click(
                locators['contentviews.select_pkg_group_checkbox']
                % package_group
            )
        if is_add:
            self.click(locators['contentviews.add_pkg_group'])
        else:
            self.click(locators['contentviews.remove_pkg_group'])

    def add_remove_errata_to_filter(self, cv_name, filter_name,
                                    errata_ids, is_add=True):
        """Add/Remove errata to/from selected filter for inclusion/exclusion"""
        self.go_to_filter_page(cv_name, filter_name)
        if is_add:
            self.click(tab_locators['contentviews.tab_add'])
        else:
            self.click(tab_locators['contentviews.tab_remove'])
        for errata_id in errata_ids:
            self.click(
                locators['contentviews.select_errata_checkbox'] % errata_id)
        if is_add:
            self.click(locators['contentviews.add_errata'])
        else:
            self.click(locators['contentviews.remove_errata'])

    def edit_erratum_date_range_filter(
            self, cv_name, filter_name, errata_types=None, date_type=None,
            start_date=None, end_date=None, open_filter=True):
        """Edit Erratum Date Range Filter"""
        allowed_errata_types = FILTER_ERRATA_TYPE.values()
        allowed_date_types = FILTER_ERRATA_DATE.values()
        if open_filter:
            self.go_to_filter_page(cv_name, filter_name)
        if errata_types is not None:
            if not errata_types:
                raise UIError(
                    'errata types is empty, minimum required: one errata type'
                )
            if not set(errata_types).issubset(allowed_errata_types):
                raise UIError('some types in errata_types are not allowed')
            # because of the behaviour of the UI to disable the last checked
            # element.
            # will check all selected errata types first, after then uncheck
            # the not selected ones.
            # 1 - check first the types that are in the errata_types
            for errata_type in errata_types:
                self.assign_value(
                    locators.contentviews.erratum_type_checkbox % errata_type,
                    True
                )
            # we are sure now that any check box not in the errata_types
            # is enabled and clickable
            # 2 - uncheck the types that are not in the selection
            for errata_type in set(allowed_errata_types).difference(
                    errata_types):
                self.assign_value(
                    locators.contentviews.erratum_type_checkbox % errata_type,
                    False
                )
        if date_type is not None:
            if date_type not in allowed_date_types:
                raise UIError('date type "{0}" not allowed'.format(date_type))
            self.click(locators.contentviews.erratum_date_type % date_type)
        if start_date is not None:
            self.set_calendar_date_value('start_date', start_date)
        if end_date is not None:
            self.set_calendar_date_value('end_date', end_date)
        self.click(locators.contentviews.save_erratum)

    def fetch_erratum_date_range_filter_values(self, cv_name, filter_name):
        """Fetch Content View Erratum Date Range Filter values"""
        self.go_to_filter_page(cv_name, filter_name)
        result = {
            'date_type': None,
            'end_date': None,
            'start_date': None,
            'types': [],
        }
        for errata_type in FILTER_ERRATA_TYPE.values():
            if self.wait_until_element(
                locators['contentviews.erratum_type_checkbox'] % errata_type
            ).is_selected():
                result['types'].append(errata_type)
        for date_type in FILTER_ERRATA_DATE.values():
            if self.wait_until_element(
                locators['contentviews.erratum_date_type'] % date_type
            ).is_selected():
                result['date_type'] = date_type
                break
        result['start_date'] = self.wait_until_element(
            locators['contentviews.calendar_date_input'] % 'start_date'
        ).get_attribute('value')
        result['end_date'] = self.wait_until_element(
            locators['contentviews.calendar_date_input'] % 'end_date'
        ).get_attribute('value')
        return result

    def fetch_puppet_module(self, cv_name, module_name):
        """Get added puppet module name from selected content-view"""
        self.search_and_click(cv_name)
        self.click(tab_locators['contentviews.tab_puppet_modules'])
        self.assign_value(common_locators['kt_search'], module_name)
        self.click(common_locators['kt_search_button'])
        return self.wait_until_element(
            locators['contentviews.get_module_name'] % module_name)

    def copy_view(self, name, new_name):
        """Copies an existing Content View."""
        self.search_and_click(name)
        self.perform_entity_action('Copy')
        self.assign_value(common_locators['copy_name_input'], new_name)
        self.click(common_locators['copy_create_button'])

    def fetch_yum_content_repo_name(self, cv_name):
        """Fetch associated yum repository info from selected content view."""
        # find content_view
        self.search_and_click(cv_name)
        self.click(tab_locators['contentviews.tab_yum_content'])
        self.click(locators['contentviews.yum_repositories'])
        if self.wait_until_element(locators['contentviews.repo_name']):
            return self.find_element(locators['contentviews.repo_name']).text
        else:
            raise UINoSuchElementError(
                'Could not get text attribute of repository locator')

    def validate_version_deleted(self, cv_name, version):
        """Ensures the version is deleted from selected CV"""
        self.search_and_click(cv_name)
        removed_version = self.find_element(
            locators['contentviews.version_name'] % version)
        if removed_version:
            raise UIError(
                'Selected version "{0}" was not deleted successfully'
                .format(version)
            )

    def validate_version_cannot_be_deleted(self, name, version):
        """Check that version cannot be deleted from selected CV, because it
        has activation key or content host assigned to it
        """
        self.search_and_click(name)
        self.click(locators['contentviews.version_dropdown'] % version)
        self.click(locators['contentviews.remove_ver'] % version)
        self.click(locators['contentviews.next_button'])
        self.wait_until_element(locators['contentviews.affected_button'])
        self.wait_for_ajax()
        self.wait_until_element(locators['contentviews.next_button'])
        self.wait_for_ajax()
        if self.is_element_enabled(locators['contentviews.next_button']):
            raise UIError(
                '"Next" button is enabled when it should not'
            )

    def version_search(self, name, version_name):
        """Search for version in content view"""
        self.search_and_click(name)
        self.click(tab_locators['contentviews.tab_versions'])
        if not bz_bug_is_open(1400535):
            self.assign_value(
                common_locators['kt_table_search'], version_name)
            self.click(common_locators['kt_table_search_button'])
        return self.wait_until_element(
            locators['contentviews.version_name'] % version_name)

    def package_search(self, name, version_name, package_name,
                       package_version=None):
        """Search for package in content view version"""
        self.click(self.version_search(name, version_name))
        self.click(tab_locators['contentviews.tab_version_packages'])
        # type package version alongside with package name into search field if
        # it was passed
        self.assign_value(
            common_locators.kt_search,
            package_name if not package_version else
            'name = "{}" and version = "{}"'.format(
                package_name,
                package_version,
            )
        )
        self.click(common_locators.kt_search_button)
        return self.wait_until_element(
            locators['contentviews.version.package_name'] % package_name)

    def fetch_version_packages(self, name, version_name):
        """Return a list of all the packages inside specific content view
        version"""
        self.click(self.version_search(name, version_name))
        self.click(tab_locators['contentviews.tab_version_packages'])
        packages = []
        while True:
            names = self.find_elements(
                locators['contentviews.version.package_name'] % '')
            versions = self.find_elements(
                locators['contentviews.version.package_version'] % '')
            releases = self.find_elements(
                locators['contentviews.version.package_release'] % '')
            for name, version, release in zip(names, versions, releases):
                packages.append((name.text, version.text, release.text))
            next_ = self.find_element(
                locators['contentviews.version.content_next_page'])
            if next_ is None:
                break
            self.click(next_)
        return packages

    def fetch_version_errata(self, name, version_name):
        """Return a list of all the errata inside specific content view
        version"""
        self.click(self.version_search(name, version_name))
        self.click(tab_locators['contentviews.tab_version_errata'])
        errata = []
        while True:
            ids = self.find_elements(
                locators['contentviews.version.errata_id'] % '')
            titles = self.find_elements(
                locators['contentviews.version.errata_title'] % '')
            types = self.find_elements(
                locators['contentviews.version.errata_type'] % '')
            for id_, title, type_ in zip(ids, titles, types):
                errata.append((id_.text, title.text, type_.text))
            next_ = self.find_element(
                locators['contentviews.version.content_next_page'])
            if next_ is None:
                break
            self.click(next_)
        return errata

    def puppet_module_search(self, name, version, module_name):
        """Search for puppet module element in content view version"""
        self.click(self.version_search(name, version))
        self.click(tab_locators.contentviews.tab_version_puppet_modules)
        self.assign_value(
            common_locators.kt_search,
            module_name
        )
        self.click(common_locators.kt_search_button)
        return self.wait_until_element(
            locators.contentviews.version.puppet_module_name % module_name)

    def remove_version_from_environments(self, name, version, environments):
        """Remove a content view version from lifecycle environments"""
        # find and open the content view
        self.search_and_click(name)
        # click on the version remove button
        self.click(locators['contentviews.version_dropdown'] % version)
        self.click(locators.contentviews.remove_ver % version)
        # ensure, that remove Completely remove version check box is unchecked
        self.assign_value(
            locators.contentviews.completely_remove_checkbox,
            False
        )
        # get all the available lifecycle environments
        all_environments_elements = self.find_elements(
            locators.contentviews.delete_version_environments)
        all_environments = [
            env_element.text
            for env_element in all_environments_elements
        ]
        # select the needed ones that are in the environments arg
        # and unselected the ones not in environments arg
        for environment in all_environments:
            self.assign_value(
                (locators.contentviews.delete_version_environment_checkbox
                 % environment),
                environment in environments
            )
        self.click(locators.contentviews.next_button)
        self.click(locators.contentviews.confirm_remove_ver)
        self.check_progress_bar_status(version)

    def get_cv_table_value(self, cv_name, column_name):
        """Get value for specific table cell

        :param str cv_name: Name of content view to be fetched
        :param str column_name: Name of table column that needs to be fetched
        :return str: Cell value text
        """
        element = self.search(cv_name)
        if element is None:
            raise UINoSuchElementError(
                'Unable to find necessary cv "{0}".'.format(cv_name)
            )
        return self.wait_until_element(
            common_locators['kt_table_cell_value'] % (cv_name, column_name)
        ).text
