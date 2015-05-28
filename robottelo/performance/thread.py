"""Test utilities for multi-threading programming"""
import logging
import threading
import time

from robottelo.performance.candlepin import Candlepin

LOGGER = logging.getLogger(__name__)


class PerformanceThread(threading.Thread):
    def __init__(self, thread_id, thread_name, time_result_dict):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.time_result_dict = time_result_dict
        self.logger = LOGGER


class DeleteThread(PerformanceThread):
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
    def __init__(self, thread_id, thread_name, time_result_dict,
                 num_iterations, ak_name, default_org, vm_ip):
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
    def __init__(self, thread_id, thread_name, time_result_dict,
                 num_iterations, sub_id, default_org, environment, vm_ip):
        super(SubscribeAttachThread, self).__init__(
            thread_id, thread_name, time_result_dict)

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

            for index in range(3):
                self.time_result_dict[self.thread_name][index].append(
                    time_points[index])
