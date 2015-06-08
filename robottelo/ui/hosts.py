"""Utilities to manipulate hosts via UI."""
from robottelo.ui.base import Base, UIError
from robottelo.common.constants import RESOURCE_DEFAULT
from robottelo.ui.locators import locators, common_locators, tab_locators
from selenium.webdriver.support.select import Select


class Hosts(Base):
    """Provides the CRUD functionality for Host."""

    def _configure_hosts(self, arch=None, custom_ptable=None, cv=None,
                         domain=None, env=None, host_group=None, ip_addr=None,
                         lifecycle_env=None, mac=None, media=None, os=None,
                         ptable=None, puppet_ca=None, puppet_master=None,
                         resource=None, root_pwd=None, subnet=None):
        # Host tab
        if lifecycle_env is not None:
            Select(
                self.wait_until_element(locators['host.lifecycle_env'])
            ).select_by_visible_text(lifecycle_env)
        if cv is not None:
            Select(
                self.wait_until_element(locators['host.cv'])
            ).select_by_visible_text(cv)
        if host_group is not None:
            Select(
                self.wait_until_element(locators['host.group'])
            ).select_by_visible_text(host_group)
        elif env is not None and host_group is None:
            # As selecting hostgroup changes env
            Select(
                self.wait_until_element(locators['host.environment'])
            ).select_by_visible_text(env)
        if puppet_ca is not None:
            Select(
                self.wait_until_element(locators['host.puppet_ca'])
            ).select_by_visible_text(puppet_ca)
        if puppet_master is not None:
            Select(
                self.wait_until_element(locators['host.puppet_master'])
            ).select_by_visible_text(puppet_master)
        # Network tab
        self.wait_until_element(tab_locators['host.tab_network']).click()
        if domain is not None:
            Select(
                self.wait_until_element(locators['host.domain'])
            ).select_by_visible_text(domain)
        if mac is not None:
            self.wait_until_element(locators['host.mac']).send_keys(mac)
        if subnet is not None:
            Select(
                self.wait_until_element(locators['host.subnet'])
            ).select_by_visible_text(subnet)
        if ip_addr is not None:
            self.wait_until_element(locators['host.ip']).send_keys(ip_addr)
        # Operating system tab
        self.wait_until_element(tab_locators['host.tab_os']).click()
        if arch is not None:
            Select(
                self.wait_until_element(locators['host.arch'])
            ).select_by_visible_text(arch)
            self.wait_for_ajax()
        if os is not None:
            Select(
                self.wait_until_element(locators['host.os'])
            ).select_by_visible_text(os)
            self.wait_for_ajax()
        if media is not None:
            Select(
                self.wait_until_element(locators['host.media'])
            ).select_by_visible_text(media)
        if ptable is not None:
            Select(
                self.wait_until_element(locators['host.ptable'])
            ).select_by_visible_text(ptable)
        if custom_ptable is not None:
            self.wait_until_element(
                locators['host.custom_ptables']).send_keys(custom_ptable)
        if root_pwd is not None:
            self.wait_until_element(
                locators['host.root_pass']).send_keys(root_pwd)

    def create(self, arch=None, cpus='1', cv=None, custom_ptable=None,
               domain=None, env=None, host_group=None, ip_addr=None,
               lifecycle_env=None, loc=None, mac=None, media=None,
               memory='768 MB', name=None, org=None, os=None, ptable=None,
               puppet_ca=None, puppet_master=None, resource=None,
               root_pwd=None, subnet=None):
        """Creates a host."""
        self.wait_until_element(locators['host.new']).click()
        self.wait_until_element(locators['host.name']).send_keys(name)
        if org is not None:
            Select(
                self.find_element(locators['host.org'])
            ).select_by_visible_text(org)
            self.wait_for_ajax()
        if loc is not None:
            Select(
                self.find_element(locators['host.loc'])
            ).select_by_visible_text(loc)
            self.wait_for_ajax()
        if resource is None:
            resource = RESOURCE_DEFAULT
        Select(
            self.wait_until_element(locators['host.deploy'])
        ).select_by_visible_text(resource)
        self._configure_hosts(
            arch=arch,
            cv=cv,
            custom_ptable=custom_ptable,
            domain=domain,
            env=env,
            host_group=host_group,
            ip_addr=ip_addr,
            lifecycle_env=lifecycle_env,
            mac=mac,
            media=media,
            os=os,
            ptable=ptable,
            puppet_ca=puppet_ca,
            puppet_master=puppet_master,
            resource=resource,
            root_pwd=root_pwd,
            subnet=subnet,
        )
        if resource != RESOURCE_DEFAULT:
            self.wait_until_element(tab_locators['host.tab_vm']).click()
            Select(
                self.wait_until_element(locators['host.vm_cpus'])
            ).select_by_visible_text(cpus)
            Select(
                self.wait_until_element(locators['host.vm_memory'])
            ).select_by_visible_text(memory)
        self.wait_until_element(common_locators['submit']).click()
        self.wait_for_ajax()

    def update(self, arch=None, cv=None, custom_ptable=None, domain=None,
               env=None, host_group=None, ip_addr=None, mac=None,
               lifecycle_env=None, media=None, name=None, new_name=None,
               os=None, ptable=None, puppet_ca=None, puppet_master=None,
               resource=None, root_pwd=None, subnet=None):
        """Updates a Host."""
        element = self.search(name)
        if element is not None:
            element.click()
            self.wait_until_element(locators['host.edit']).click()
            self.wait_for_ajax()
            if new_name is not None:
                self.wait_until_element(locators['host.name'])
                self.field_update('host.name', new_name)
            self._configure_hosts(
                arch=arch,
                cv=cv,
                custom_ptable=custom_ptable,
                domain=domain,
                env=env,
                host_group=host_group,
                ip_addr=ip_addr,
                lifecycle_env=lifecycle_env,
                mac=mac,
                media=media,
                os=os,
                ptable=ptable,
                puppet_ca=puppet_ca,
                puppet_master=puppet_master,
                resource=resource,
                root_pwd=root_pwd,
                subnet=subnet,
            )
            self.find_element(common_locators['submit']).click()
            self.wait_for_ajax()
        else:
            raise UIError('Could not update the host "{0}"'.format(name))

    def search(self, name):
        """Searches existing host from UI."""
        return self.search_entity(name, locators['host.select_name'])

    def delete(self, name, really):
        """Deletes a host."""
        self.delete_entity(
            name,
            really,
            locators['host.select_name'],
            locators['host.delete'],
            drop_locator=locators['host.dropdown']
        )
