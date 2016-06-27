# -*- encoding: utf-8 -*-
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UINoSuchElementError, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Container(Base):
    """Provides the CRUD functionality for Docker Containers."""

    def navigate_to_entity(self):
        """Navigate to All Containers page"""
        Navigator(self.browser).go_to_all_containers()

    def _search_locator(self):
        """Specify locator for Container entity search procedure"""
        return locators['container.search_entity']

    def _configure_orgs(self, orgs, org_select):
        """Provides configuration capabilities for docker container
        organization. The following format should be used::

            orgs=['Aoes6V', 'JIFNPC'], org_select=True

        """
        self.configure_entity(
            orgs,
            FILTER['container_org'],
            tab_locator=tab_locators['tab_org'],
            entity_select=org_select,
        )

    def _configure_locations(self, locations, loc_select):
        """Provides configuration capabilities for docker container location

        The following format should be used::

            locations=['Default Location'], loc_select=True

        """
        self.configure_entity(
            locations,
            FILTER['container_loc'],
            tab_locator=tab_locators['tab_loc'],
            entity_select=loc_select,
        )

    def _form_locator_name(self, partial_locator):
        """Form locator using provided friendly UI name, e.g. 'Content View'"""
        return '.'.join((
            'container',
            (partial_locator.lower()).replace(' ', '_')
        ))

    def create(self, resource_name, name, command, parameter_list):
        """Creates a docker container. All values should be passed in absolute
        correspondence to UI. Parameters names created in self-descriptive
        manner. Of course, we can easily expand list of parameters and create
        custom flows for specific situations. Here are some examples of
        parameter_list values from each main tab::

            [
                {'main_tab_name': 'Preliminary', 'sub_tab_name': 'Location',
                'name': ['Default Location']},
                {'main_tab_name': 'Image', 'sub_tab_name': 'Content View',
                'name': 'Lifecycle Environment', 'value': self.lce.name},
                {'main_tab_name': 'Image', 'sub_tab_name': 'Docker Hub',
                'name': 'Docker Hub Tag', 'value': 'latest'},
                {'main_tab_name': 'Configuration', 'name': 'Memory',
                'value': '512m'},
                {'main_tab_name': 'Environment', 'name': 'TTY', 'value': True},
            ]
        """
        # send_keys() can't send left parenthesis (see SeleniumHQ/selenium#674)
        # which is used in compute resource name (e.g. 'test (Docker)')
        if ' (' in resource_name:
            self.click(locators['container.resource_name'])
            # typing compute resource name without parenthesis part
            self.text_field_update(
                common_locators['select_list_search_box'],
                resource_name.split(' (')[0]
            )
            strategy, value = common_locators['entity_select_list']
            # selecting compute resource by its full name (with parenthesis
            # part)
            self.click((strategy, value % resource_name))
        else:
            self.assign_value(
                locators['container.resource_name'], resource_name)
        for parameter in parameter_list:
            if parameter['main_tab_name'] == 'Preliminary':
                if parameter['sub_tab_name'] == 'Organization':
                    self._configure_orgs(parameter['name'], True)
                elif parameter['sub_tab_name'] == 'Location':
                    self._configure_locations(parameter['name'], True)
        self.click(locators['container.next_section'])
        current_tab = self._form_locator_name('Content View Tab')
        for parameter in parameter_list:
            if parameter['main_tab_name'] == 'Image':
                current_tab = self._form_locator_name(
                    parameter['sub_tab_name'] + ' Tab')
                self.click(locators[current_tab])
                self.assign_value(
                    locators[
                        self._form_locator_name(
                            'registry.' + parameter['name'])
                    ]
                    if parameter['sub_tab_name'] == 'External registry' else
                    locators[self._form_locator_name(parameter['name'])],
                    parameter['value']
                )
        self.click(locators[current_tab + '_next'])
        self.assign_value(locators['container.name'], name)
        self.assign_value(locators['container.command'], command)
        for parameter in parameter_list:
            if parameter['main_tab_name'] == 'Configuration':
                self.assign_value(
                    locators[self._form_locator_name(parameter['name'])],
                    parameter['value']
                )
        self.click(locators['container.next_section'])
        self.browser.refresh()
        for parameter in parameter_list:
            if parameter['main_tab_name'] == 'Environment':
                self.assign_value(
                    locators[self._form_locator_name(parameter['name'])],
                    parameter['value']
                )
        self.click(locators['container.next_section'])
        strategy, value = locators['container.created_container_name']
        element = self.wait_until_element((strategy, value % name))
        if element is None:
            raise UINoSuchElementError(
                'Container with name {0} was not created successfully'
                .format(name)
            )

    def search(self, resource_name, container_name):
        """Searches for existing container from particular compute resource. It
        is necessary to use custom search here as we need to select compute
        resource tab before searching for particular container and also, there
        is no search button to click

        """
        self.navigate_to_entity()
        strategy, value = locators['container.resource_search_tab']
        self.click((strategy, value % resource_name))
        self.text_field_update(
            locators['container.search_filter'], container_name)
        strategy, value = self._search_locator()
        return self.wait_until_element((strategy, value % container_name))

    def delete(self, resource_name, container_name, really=True):
        """Removes the container entity"""
        element = self.search(resource_name, container_name)
        if element is None:
            raise UIError(
                'Could not find container "{0}"'.format(container_name))
        element.click()
        self.wait_for_ajax()
        self.click(locators['container.delete'], wait_for_ajax=False)
        self.handle_alert(really)

    def set_power_status(self, resource_name, cont_name, power_on):
        """Perform power on or power off for container

        :param bool power_on: True - for On, False - for Off

        """
        status = None
        locator_on = (locators['container.power_on'][0],
                      locators['container.power_on'][1] % cont_name)
        locator_off = (locators['container.power_off'][0],
                       locators['container.power_off'][1] % cont_name)
        locator_status = (locators['container.power_status'][0],
                          locators['container.power_status'][1] % cont_name)
        element = self.search(resource_name, cont_name)
        if element is None:
            raise UIError(
                'Could not find container "{0}"'.format(cont_name))
        self.wait_for_ajax()
        if power_on is True:
            self.click(locator_on)
            self.search(resource_name, cont_name)
            if self.wait_until_element(locator_off):
                status = self.wait_until_element(locator_status).text
        elif power_on is False:
            self.click(locator_off, wait_for_ajax=False)
            self.handle_alert(True)
            self.search(resource_name, cont_name)
            if self.wait_until_element(locator_on):
                status = self.wait_until_element(locator_status).text
        return status
