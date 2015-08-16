"""Test utilities for multi-threading programming"""
import logging
import threading
import time

from robottelo.performance.candlepin import Candlepin
from robottelo.performance.pulp import Pulp

LOGGER = logging.getLogger(__name__)


class PerformanceThread(threading.Thread):
    """Parent thread for all performance concurrent test

    All tests of concurrent subscription by activation-key/attach,
    concurrent deletion, concurrent synchronization would kick off
    multiple threads to measure timing latency.

    """
    def __init__(self, thread_id, thread_name, time_result_dict):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.time_result_dict = time_result_dict
        self.logger = LOGGER


class DeleteThread(PerformanceThread):
    """Thread utility to support concurrent content hosts deletion"""
    def __init__(self, thread_id, thread_name, sublist, time_result_dict):
        super(DeleteThread, self).__init__(
            thread_id, thread_name, time_result_dict)
        self.sublist = sublist

    def run(self):
        time.sleep(5)
        self.logger.debug('Start timing in thread {}'.format(self.thread_id))
        for idx, uuid in enumerate(self.sublist):
            if uuid != '':
                self.logger.debug(
                    'deletion attempt # {0} in thread {1}-uuid: {2}'
                    .format(idx, self.thread_id, uuid))
                # conduct one request by the id
                time_point = Candlepin.single_delete(uuid, self.thread_id)
                self.time_result_dict[self.thread_name].append(time_point)


class SubscribeAKThread(PerformanceThread):
    """Thread utility to support concurrent subscription by activation key"""
    def __init__(
            self,
            thread_id,
            thread_name,
            time_result_dict,
            num_iterations,
            ak_name,
            default_org,
            vm_ip):
        super(SubscribeAKThread, self).__init__(
            thread_id, thread_name, time_result_dict)
        self.num_iterations = num_iterations
        self.ak_name = ak_name
        self.default_org = default_org
        self.vm_ip = vm_ip

    def run(self):
        time.sleep(5)
        for i in range(self.num_iterations):
            self.logger.debug(
                "{0}: register with ak {1} on {2} attempt {3}"
                .format(self.thread_name, self.ak_name, self.vm_ip, i))
            time_point = Candlepin.single_register_activation_key(
                self.ak_name,
                self.default_org,
                self.vm_ip)
            self.time_result_dict[self.thread_name].append(time_point)


class SubscribeAttachThread(PerformanceThread):
    """Thread for Subscription by register and attach

    separate `time_result_dictionary` into two new dictionaries:
    time_result_dict_register, containing timing results of register step
    time_result_dict_attach, containing timing results of attach step

    The data structure of dictionaries now is::

        dict-register: {client-0: [...], ..., client-9:[...]}
        dict-attach: {client-0: [...], ..., client-9:[...]}

    """
    def __init__(
            self,
            thread_id,
            thread_name,
            time_result_dict,
            time_result_dict_register,
            time_result_dict_attach,
            num_iterations,
            sub_id,
            default_org, environment,
            vm_ip):
        super(SubscribeAttachThread, self).__init__(
            thread_id,
            thread_name,
            time_result_dict
        )

        self.time_result_dict_register = time_result_dict_register
        self.time_result_dict_attach = time_result_dict_attach
        self.num_iterations = num_iterations
        self.sub_id = sub_id
        self.default_org = default_org
        self.environment = environment
        self.vm_ip = vm_ip

    def run(self):
        for i in range(self.num_iterations):
            self.logger.debug(
                "{0}: register with subscription {1} on vm {2} attempt {3}"
                .format(self.thread_name, self.sub_id, self.vm_ip, i))

            time_points = Candlepin.single_register_attach(
                self.sub_id,
                self.default_org,
                self.environment,
                self.vm_ip)

            # split original time_result_dict into two new dictionaries
            # append each client's register timing data
            self.time_result_dict_register.get(
                self.thread_name, 'thread-0'
            ).append(time_points[0])

            # append each client's attach timing data
            self.time_result_dict_attach.get(
                self.thread_name, 'thread-0'
            ).append(time_points[1])


class SyncThread(PerformanceThread):
    """Thread utility to support concurrent synchronization"""
    def __init__(
            self,
            thread_id,
            thread_name,
            time_result_dict,
            repository_id,
            repository_name,
            iteration):
        super(SyncThread, self).__init__(
            thread_id,
            thread_name,
            time_result_dict
        )
        self.repository_id = repository_id
        self.repository_name = repository_name
        self.iteration = iteration

    def run(self):
        LOGGER.debug(
            "{0}: synchronize repository {1} attempt {2}"
            .format(self.thread_name, self.repository_name, self.iteration)
        )

        time_point = Pulp.repository_single_sync(
            self.repository_id,
            self.repository_name,
            self.thread_id,
        )

        # append sync timing to each thread
        self.time_result_dict.get(self.thread_name).append(time_point)
