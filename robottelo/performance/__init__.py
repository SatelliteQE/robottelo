"""This package contains helper code used by tests.foreman.performance.

This module is subservient to tests.foreman.performance, and exists soley for
the sake of helping that module get its work done. For example,
tests.foreman.performance.test_candlepin_concurrent_delete relies upon
perf_stat to generate csv files. More generally: code in test calls code
in this common module, but not the other way around.

"""
