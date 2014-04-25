import os
import re

from robottelo.common import conf, ssh


LOGS_DATA_DIR = os.path.join(conf.get_root_path(), 'data', 'logs')


class LogFile(object):
    def __init__(self, remote_path, pattern=None):
        self.remote_path = remote_path
        self.pattern = pattern

        if not os.path.isdir(LOGS_DATA_DIR):
            os.makedirs(LOGS_DATA_DIR)
        self.local_path = os.path.join(LOGS_DATA_DIR,
                                       os.path.basename(remote_path))
        ssh.download_file(remote_path, self.local_path)
        with open(self.local_path) as f:
            self.data = f.readlines()

    def filter(self, pattern=None):
        """Filter the log file using the pattern argument or object pattern"""

        if pattern is None:
            pattern = self.pattern

        compiled = re.compile(pattern)

        result = []

        for line in self.data:
            if compiled.search(line) is not None:
                result.append(line)

        return result
