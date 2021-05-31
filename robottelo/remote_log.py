"""Utilities to help work with log files"""
import os
import re

from robottelo import ssh
from robottelo.config import robottelo_root_dir

LOGS_DATA_DIR = os.path.join(robottelo_root_dir, 'data', 'logs')


class LogFile:
    """
    References a remote log file. The log file will be downloaded to allow
    operate on it using python
    """

    def __init__(self, remote_path, pattern=None):
        self.remote_path = remote_path
        self.pattern = pattern

        if not os.path.isdir(LOGS_DATA_DIR):
            os.makedirs(LOGS_DATA_DIR)
        self.local_path = os.path.join(LOGS_DATA_DIR, os.path.basename(remote_path))
        ssh.download_file(remote_path, self.local_path)
        with open(self.local_path) as file_:
            self.data = file_.readlines()

    def filter(self, pattern=None):
        """
        Filter the log file using the pattern argument or object's pattern
        """

        if pattern is None:
            pattern = self.pattern

        compiled = re.compile(pattern)

        result = []

        for line in self.data:
            if compiled.search(line) is not None:
                result.append(line)

        return result
