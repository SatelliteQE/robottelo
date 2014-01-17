# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class ComputeResource(Base):
    """
    Provides the CRUD functionality for Compute Resources.
    """

    def __init__(self, browser):
        self.browser = browser

    def _configure_resource(self, provider_type, url,
                            user, password, region,
                            libvirt_display, tenant,
                            libvirt_set_passwd):
        """
        Configures the compute resource.
        """
        if provider_type:
            type_ele = self.find_element(locators["resource.provider_type"])
            Select(type_ele).select_by_visible_text(provider_type)
            if provider_type in ["EC2", "Rackspace", "Openstack"]:
                if provider_type in ["Rackspace", "Openstack"]:
                    self.find_element(locators["resource.url"]).send_keys(url)
                access = self.find_element(locators["resource.user"])
                access.send_keys(user)
                secret = self.find_element(locators["resource.password"])
                secret.send_keys(password)
                self.find_element(locators["resource.test_connection"]).click()
                self.wait_for_ajax()
                if provider_type in ["Rackspace", "EC2"]:
                    region = self.find_element(locators["resource.region"])
                    Select(region).select_by_visible_text(region)
                elif provider_type == "Openstack":
                    tenant = self.find_element(locators["resource.rhos_tenant"])  # @IgnorePep8
                    Select(tenant).select_by_visible_text(tenant)

            if provider_type == "Libvirt":
                if self.wait_until_element(locators["resource.url"]):
                    self.find_element(locators["resource.url"]).send_keys(url)
        if libvirt_display is not None:
            display = self.find_element(locators["resource.libvirt_display"])
            Select(display).select_by_visible_text(libvirt_display)
        if libvirt_set_passwd is False:
            self.find_element(locators["resource.libvirt_console_passwd"]).click()  # @IgnorePep8
        self.find_element(locators["resource.test_connection"]).click()
        self.wait_for_ajax()
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()

    def create(self, name, provider_type=None, url=None, user=None,
               password=None, region=None, libvirt_display=None,
               libvirt_set_passwd=True, tenant=None):
        """
        Creates a compute resource.
        """
        self.wait_until_element(locators["resource.new"]).click()
        if self.wait_until_element(locators["resource.name"]):
            self.find_element(locators["resource.name"]).send_keys(name)
        self._configure_resource(provider_type, url, user, password, region,
                                 libvirt_display, tenant, libvirt_set_passwd)

    def search(self, name):
        """
        Searches existing compute resource from UI
        """
        element = self.search_entity(name, locators["resource.select_name"])
        return element

    def update(self, oldname, newname, provider_type=None, url=None, user=None,
               password=None, region=None, libvirt_display=None,
               libvirt_set_passwd=True, tenant=None):
        """
        Updates a compute resource.
        """
        element = self.search(oldname)
        if element:
            element.click()
            strategy = locators["resource.edit"][0]
            value = locators["resource.edit"][1]
            edit = self.wait_until_element((strategy, value % oldname))
            edit.click()
            if self.wait_until_element(locators["resource.name"]) and newname:
                self.field_update("resource.name", newname)
            self._configure_resource(provider_type, url, user, password,
                                     region, libvirt_display, tenant,
                                     libvirt_set_passwd)
        else:
            raise Exception("Could not update the resource '%s'" % oldname)

    def delete(self, name, really):
        """
        Removes the compute resource info.
        """

        self.delete_entity(name, really, locators["resource.select_name"],
                           locators['resource.delete'],
                           drop_locator=locators["resource.dropdown"])
