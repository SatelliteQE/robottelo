# -*- encoding: utf-8 -*-
"""Implements Job Template UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class JobTemplate(Base):
    """Provides the CRUD functionality for Job Templates."""

    def navigate_to_entity(self):
        """Navigate to Job Template entity page"""
        Navigator(self.browser).go_to_job_templates()

    def _search_locator(self):
        """Specify locator for Job Template entity search procedure"""
        return locators['job.template_select']

    def _configure_job_template(self, default=None, audit_comment=None,
                                job_category=None, description_format=None,
                                provider_type=None, effective_user_value=None,
                                current_user=None, overridable=None,
                                snippet=None):
        """Configures different entities of selected job template."""
        self.click(tab_locators['tab_primary'])
        if default:
            self.assign_value(locators['job.template_default'], default)
        if audit_comment:
            self.assign_value(
                locators['job.audit_comment'], audit_comment)
        self.click(tab_locators['job.tab_job'])
        if job_category:
            self.assign_value(locators['job.job_category'], job_category)
        if description_format:
            self.assign_value(
                locators['job.description_format'], description_format)
        if provider_type:
            self.assign_value(locators['job.provider_type'], provider_type)
        if effective_user_value:
            self.assign_value(
                locators['job.effective_user_value'], effective_user_value)
        if current_user:
            self.assign_value(locators['job.current_user'], current_user)
        if overridable:
            self.assign_value(
                locators['job.effective_user_overridable'], overridable)
        if snippet:
            self.click(tab_locators['job.tab_type'])
            self.assign_value(locators['job.template_snippet'], snippet)

    def create(self, name, template_content, template_type=None, default=None,
               audit_comment=None, job_category=None, description_format=None,
               provider_type=None, effective_user_value=None,
               current_user=None, overridable=None, snippet=None):
        """Creates a job template from UI."""
        self.click(locators['job.template_new'])
        self.click(tab_locators['tab_primary'])
        self.assign_value(locators['job.template_name'], name)
        if template_type == 'file':
            self.wait_until_element(
                locators['job.template_file']).send_keys(template_content)
            self.handle_alert(True)
        elif template_type == 'input':
            self.assign_value(locators['job.template_input'], template_content)
        self._configure_job_template(
            default=default, audit_comment=audit_comment,
            job_category=job_category, description_format=description_format,
            provider_type=provider_type,
            effective_user_value=effective_user_value,
            current_user=current_user, overridable=overridable,
            snippet=snippet
        )
        self.click(common_locators['submit'])

    def update(self, name, new_name=None, template_content=None,
               template_type=None, default=None, audit_comment=None,
               job_category=None, description_format=None, provider_type=None,
               effective_user_value=None, current_user=None, overridable=None,
               snippet=None):
        """Updates a job template from UI."""
        self.click(self.search(name))
        self.click(tab_locators['tab_primary'])
        if new_name:
            self.assign_value(locators['job.template_name'], new_name)
        if template_content:
            if template_type == 'file':
                self.assign_value(
                    locators['job.template_file'], template_content)
                self.handle_alert(True)
            elif template_type == 'input':
                self.assign_value(
                    locators['job.template_input'], template_content)
        self._configure_job_template(
            default=default, audit_comment=audit_comment,
            job_category=job_category, description_format=description_format,
            provider_type=provider_type,
            effective_user_value=effective_user_value,
            current_user=current_user, overridable=overridable,
            snippet=snippet
        )
        self.click(common_locators['submit'])

    def add_input(self, job_template_name, name, required=None,
                  input_type='User input', advanced=None, options=None,
                  description=None):
        """Add new input to existing job template. At that moment only 'user
        input' type is supported, but method can be expanded to support all
        types
        """
        self.click(self.search(job_template_name))
        self.click(tab_locators['job.tab_job'])
        self.click(locators['job.add_new_input'])
        self.assign_value(locators['job.input_name'], name)
        if required:
            self.assign_value(locators['job.input_required'], required)
        self.assign_value(locators['job.input_input_type'], input_type)
        if advanced:
            self.assign_value(locators['job.input_advanced'], advanced)
        if options:
            self.assign_value(locators['job.input_options'], options)
        if description:
            self.assign_value(locators['job.input_description'], description)
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Deletes job template."""
        self.delete_entity(
            name,
            really,
            locators['job.template_delete'],
            drop_locator=locators['job.template_dropdown'],
        )

    def clone(
            self, name, clone_name, template_content=None, template_type=None):
        """Clones a given job template."""
        self.search(name)
        self.click(locators['job.template_dropdown'] % name)
        self.click(locators['job.template_clone'])
        self.assign_value(locators['job.template_name'], clone_name)
        if template_content:
            if template_type == 'file':
                self.assign_value(
                    locators['job.template_file'], template_content)
                self.handle_alert(True)
            elif template_type == 'input':
                self.assign_value(
                    locators['job.template_input'], template_content)
        self.click(common_locators['submit'])
