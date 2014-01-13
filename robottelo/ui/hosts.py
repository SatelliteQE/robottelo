
from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from selenium.webdriver.support.select import Select


class Hosts(Base):
    """
    Provides the CRUD functionality for Host.
    """
    def __init__(self, browser):
        self.browser = browser

    def create(self, name, domain, subnet, host_group=None, resource=None,
               env=None, ip_addr=None, mac=None, os=None, arch=None,
               media=None, ptable=None, custom_ptable=None, root_pwd=None,
               cpus="1", memory="768 MB"):
        """
        Creates a host.
        """
        self.wait_until_element(locators["host.new"]).click()
        if self.wait_until_element(locators["host.name"]):
            self.find_element(locators["host.name"]).send_keys(name)
        if resource is None:
            resource = "baremetal"
        type_deploy = self.find_element(locators["host.deploy"])
        Select(type_deploy).select_by_visible_text(resource)
        if host_group:
            type_ele = self.find_element(locators["host.group"])
            Select(type_ele).select_by_visible_text(host_group)
        elif env and host_group is None:  # As selecting hostgroup changes env
            type_env = self.find_element(locators["host.environment"])
            Select(type_env).select_by_visible_text(env)

        if domain:
            if resource is None:
                self.find_element(locators["host.mac"]).send_keys(mac)
            self.wait_until_element(tab_locators["host.tab_network"]).click()
            type_domain = self.find_element(locators["host.domain"])
            Select(type_domain).select_by_visible_text(domain)
            self.wait_for_ajax()
            type_subnet = self.find_element(locators["host.subnet"])
            Select(type_subnet).select_by_visible_text(subnet)
            if ip_addr:
                self.find_element(locators["host.ip"]).send_keys(ip_addr)
        if os:
            self.wait_until_element(tab_locators["host.tab_os"]).click()
            type_arch = self.find_element(locators["host.arch"])
            Select(type_arch).select_by_visible_text(arch)
            self.wait_for_ajax()
            type_os = self.find_element(locators["host.os"])
            Select(type_os).select_by_visible_text(os)
            self.wait_for_ajax()
            type_media = self.find_element(locators["host.media"])
            Select(type_media).select_by_visible_text(media)
            self.wait_for_ajax()
            type_ptable = self.find_element(locators["host.ptable"])
            Select(type_ptable).select_by_visible_text(ptable)
            self.wait_for_ajax()
            if custom_ptable:
                custom = self.find_element(locators["host.custom_ptables"])
                custom.send_keys(custom_ptable)
            password = self.find_element(locators["host.root_pass"])
            password.send_keys(root_pwd)
            self.find_element(locators["host.provision_template"]).click()
            self.wait_for_ajax()

        if resource is not None:
            self.wait_until_element(tab_locators["host.tab_vm"]).click()
            vm_cpu = self.find_element(locators["host.vm_cpus"])
            Select(vm_cpu).select_by_visible_text(cpus)
            vm_mem = self.find_element(locators["host.vm_memory"])
            Select(vm_mem).select_by_visible_text(memory)
        self.find_element(common_locators["submit"]).click()

    def delete(self, name, really):
        """
        Deletes a host.
        """

        self.delete_entity(name, really, locators["host.select_name"],
                           locators['host.delete'],
                           drop_locator=locators["host.dropdown"])
