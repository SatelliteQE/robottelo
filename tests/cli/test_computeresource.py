#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""
Usage:
    hammer compute_resource [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a compute resource.
    info                          Show an compute resource.
    list                          List all compute resources.
    update                        Update a compute resource.
    delete                        Delete a compute resource.
    image                         View and manage compute resource's images
"""
from ddt import data
from ddt import ddt
from robottelo.cli.computeresource import ComputeResource
from robottelo.common import conf
from robottelo.common.helpers import generate_name, sleep_for_seconds
from robottelo.cli.factory import make_compute_resource
from robottelo.common.constants import FOREMAN_PROVIDERS
from tests.cli.basecli import BaseCLI


@ddt
class TestComputeResource(BaseCLI):
    """
    ComputeResource CLI tests.
    """

    def _init_once(self):
        """ a method invoked only once """
        self.__class__.comp_res = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})['name']

    def test_create(self):
        """ `compute_resource create` basic test """
        name = generate_name(8, 8)
        result = ComputeResource().create({
            'name': name,
            'provider': 'Libvirt',
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']
        })
        self.assertEquals(result.return_code, 0,
                          "ComputeResource create - exit code")

    def test_info(self):
        """ `compute_resource info` basic test """
        result_create = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})
        self.assertTrue(result_create['name'],
                        "ComputeResource create - has name")
        sleep_for_seconds(5)
        result_info = ComputeResource().info({'name': result_create['name']})
        self.assertEquals(result_info.return_code, 0,
                          "ComputeResource info - exit code")
        self.assertEquals(result_info.stdout['Name'], result_create['name'],
                          "ComputeResource info - check name")

    def test_list(self):
        """ `compute_resource list` basic test """
        result_create = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})
        self.assertTrue(result_create['name'],
                        "ComputeResource create - has name")
        result_list = ComputeResource().list()
        self.assertEquals(result_list.return_code, 0,
                          "ComputeResource list - exit code")
        self.assertTrue(len(result_list.stdout) > 0,
                        "ComputeResource list - stdout has results")
        self.assertTrue(
            ComputeResource().exists(
                ('name', result_create['name'])
            ),
            "ComputeResource list - exists name")

    @data(
        {'description': "updated: compute resource"},
        {'url': "qemu+tcp://localhost:16509/system"},
        {
            'provider': FOREMAN_PROVIDERS['ovirt'],
            'description': 'updated to Ovirt',
            'url': "https://localhost:443/api",
            'user': 'admin@internal',
            'password': "secret"
         }
    )
    def test_update(self, option_dict):
        """ `compute_resource update` basic test (different options) """
        options = {}
        options['name'] = self.comp_res
        for option in option_dict:
            options[option] = option_dict[option]
        result_update = ComputeResource().update(options)
        self.assertEquals(result_update.return_code, 0,
                          "ComputeResource update - exit code")

    def test_delete(self):
        """ `compute_resource delete` basic test """
        result_create = make_compute_resource({
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': "qemu+tcp://%s:16509/system" %
            conf.properties['main.server.hostname']})
        self.assertTrue(result_create['name'],
                        "ComputeResource create - has name")
        sleep_for_seconds(5)
        result_delete = ComputeResource().delete(
            {'name': result_create['name']})
        self.assertEquals(
            result_delete.return_code, 0,
            "ComputeResource delete - exit code")
        sleep_for_seconds(5)
        self.assertFalse(
            ComputeResource().exists(
                ('name', result_create['name'])),
            "ComputeResource list - does not exist name")
