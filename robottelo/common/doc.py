# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
DocString manipulation methods to create test reports
"""

import ast
import os
import sys

from robottelo.common.constants import CLI_TESTS
from robottelo.common.constants import DOCSTRING_TAGS
from robottelo.common.constants import UI_TESTS
from robottelo.common.helpers import get_root_path

bugs = 0
bug_list = []
invalid_doc_string = 0
manual_count = 0
no_doc_string = 0
tc_count = 0


def main():
    """
    Function to get all the test files in a directory and retrieve
    their docstrings
    1 - Print all test cases
    2 - Summary of number of automated cases vs. manual cases
    3 - validate docstrings
    4 - Test cases affected by Bugs and the Bug list
    5 - List all manual test cases
    6 - List all auto test cases

    Expected Docstring format:
    @Feature: SSO - Active Directory
    @Test: Log in with valid Active Directory credentials
    @Setup: Install foreman and configure with Active Directory
    @Steps:
      1.  Launch the foreman UI
      2.  Log in with valid Active Dir
    @Assert: Log in to foreman UI successfully
    @BZ: #1234567
    @Status: Manual (or simply remove this field once automated)

    Usage:
    # python robottelo/common/doc.py 1

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------

    Analysing test_sample.py...
    TC 1
    Feature: SSO - Active Directory
    Test: Log in with valid Active Directory credentials
    Setup: Install foreman and configure with Active Directory
    Steps:
        1.  Launch the foreman UI
        2.  Log in with valid Active Dir
    Assert: Log in to foreman UI successfully
    BZ: #1234567
    Status: Manual (or simply remove this field once automated)

    # python robottelo/common/doc.py 2

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Total Number of test cases:      5
    Total Number of automated cases: 4
    Total Number of manual cases:    1
    Test cases with no docstrings:   0

    TEST PATH: /home/framework/robottelo/tests/cli/
    ----------------------------------------------------------------
    Total Number of test cases:      0
    Total Number of automated cases: 0
    Total Number of manual cases:    0
    Test cases with no docstrings:   0

    # python robottelo/common/doc.py 3

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Analyzing test_sample.py...
    -->Invalid DocString: Creates new domain and delete it<--
    -->Invalid DocString: Create new domain and update its name, description<--
    -->Invalid DocString: Set domain parameter<--
    -->Invalid DocString: Remove selected domain parameter<--
    Total Number of invalid docstrings:  4

    # python robottelo/common/doc.py 4

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Analyzing test_sample.py...
    Total Number of test cases affected by bugs: 1
    List of bugs:                                ['#1234567']

    python robottelo/common/doc.py 5

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Analyzing test_sample.py...
    Feature: SSO - Active Directory
    Test: Log in with valid Active Directory credentials
    Setup: Install foreman and configure with Active Directory
    Steps:
        1.  Launch the foreman UI
        2.  Log in with valid Active Dir
    Assert: Log in to foreman UI successfully
    BZ: #1234567
    Status: Manual (or simply remove this field once automated)

    # python robottelo/common/doc.py 6

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Analyzing test_sample.py...
    Creates new domain and deletes it
    Create new domain and update its name, description
    Set domain parameter
    Remove selected domain parameter
    """
    global bug_list
    global bugs
    global invalid_doc_string

    for input_path in (UI_TESTS, CLI_TESTS):
        reset_counts()
        path = get_root_path() + input_path
        print "\nTEST PATH: %s" % path
        print "--------------------------------------------------------------"
        for root, dirs, files in os.walk(path):
            for i in range(1, len(files)):
                if str(files[i]).startswith('test') and str(files[i]).endswith('.py'):  # @IgnorePep8
                    #Do not print this text for test summary
                    if sys.argv[1] != "2":
                        print "Analyzing %s..." % files[i]
                    filepath = path + files[i]
                    list_strings = get_docstrings(filepath)
                    if sys.argv[1] == "1" or sys.argv[1] == "3" or sys.argv[1] == "4":  # @IgnorePep8
                        #print the derived test cases
                        print_testcases(list_strings)
                    elif sys.argv[1] == "5":
                        #print manual test cases
                        print_testcases(list_strings, test_type="manual")
                    elif sys.argv[1] == "6":
                        #print auto test cases
                        print_testcases(list_strings, test_type="auto")
                    else:
                        #for printing test summary later
                        update_summary(list_strings)
        #Print for test summary
        if sys.argv[1] == "2":
            print_summary()
        #Print total number of invalid doc strings
        if sys.argv[1] == "3":
            print "Total Number of invalid docstrings:  %d" % invalid_doc_string  # @IgnorePep8
        #Print number of test cases affected by bugs and also the list of bugs
        if sys.argv[1] == "4":
            print "Total Number of test cases affected by bugs: %d" % bugs
            print "List of bugs:                               ", bug_list


def get_docstrings(path):
    """
    Function to read docstrings from test_*** methods for a given file
    """
    global no_doc_string
    global invalid_doc_string
    global bugs
    global bug_list
    return_list = []
    obj = ast.parse(''.join(open(path)))
    for i in range(0, len(obj.body)):
        parameters = obj.body[i]._fields
        for attr in parameters:
            if attr == 'body':
                break
    for j in range(0, len(obj.body[i].body)):
        try:
            obj_param = obj.body[i].body[j]._fields
            for attr in obj_param:
                if attr == 'name':
                    func_name = getattr(obj.body[i].body[j], "name")
                    if func_name.startswith('test'):
                        value = obj.body[i].body[j].body[0].value.s.lstrip()
                        doclines = value.split('@',)
                        item_list = []
                        for attr in doclines:
                            attr = attr.rstrip()
                            attr = attr.rstrip('\n')
                            if attr != '':
                                if sys.argv[1] == "3":
                                    docstring_tag = attr.split(" ", 1)
                                    if not any(x in docstring_tag[0] for x in DOCSTRING_TAGS):  # @IgnorePep8
                                        item_list.append("-->Invalid DocString: %s<--" % attr)  # @IgnorePep8
                                        invalid_doc_string = invalid_doc_string + 1  # @IgnorePep8
                                elif sys.argv[1] == "4":
                                    docstring_tag = attr.split(" ", 1)
                                    if DOCSTRING_TAGS[5] in docstring_tag[0]:
                                        item_list.append(attr)
                                        bugs = bugs + 1
                                        bug_list.append(docstring_tag[1])
                                else:
                                    item_list.append(attr)
                        if len(item_list) != 0:
                            return_list.append(item_list)
        except AttributeError:
            if sys.argv[1] == '1' or sys.argv[1] == "3":
                print "--> DocString Missing. Please update <--"
            no_doc_string = no_doc_string + 1
            continue
        except:
            print "!!!!!Exception in parsing DocString!!!!!"
    return return_list


def print_testcases(list_strings, test_type=None):
    """
    Prints all the test cases based on given criteria
    """
    tc = 0
    for docstring in list_strings:
        if sys.argv[1] == "1":
            tc = tc + 1
            print "TC %d" % tc

        #verify if this needs to be printed
        if test_type is not None:
            manual_print = False
            auto_print = True
            for lineitem in docstring:
                docstring_tag = lineitem.split(" ", 1)
                if test_type == "auto":
                    if DOCSTRING_TAGS[6] in docstring_tag[0]:
                        auto_print = False
                if test_type == "manual":
                    if DOCSTRING_TAGS[6] in docstring_tag[0]:
                        manual_print = True
        if test_type == "auto" and auto_print is True:
            print_line_item(docstring)
        if test_type == "manual" and manual_print is True:
            print_line_item(docstring)
        if sys.argv[1] == "1" or sys.argv[1] == "3":
            print_line_item(docstring)


def update_summary(list_strings):
    """
    Updates summary for reporting
    """
    global tc_count
    global manual_count
    for docstring in list_strings:
        tc_count = tc_count + 1
        for lineitem in docstring:
            if lineitem.startswith("Status") and "Manual" in lineitem:
                manual_count = manual_count + 1


def print_summary():
    """
    Prints summary for reporting
    """
    global tc_count
    global manual_count
    global no_doc_string
    print "Total Number of test cases:      %d" % tc_count
    print "Total Number of automated cases: %d" % (tc_count - manual_count)
    print "Total Number of manual cases:    %d" % manual_count
    print "Test cases with no docstrings:   %d" % no_doc_string


def reset_counts():
    """
    Resets all the counts to switch between UI and CLI reports
    """
    global tc_count
    global manual_count
    global no_doc_string
    global invalid_doc_string
    global bugs
    global bug_list
    tc_count = 0
    manual_count = 0
    no_doc_string = 0
    invalid_doc_string = 0
    bugs = 0
    bug_list = []


def print_line_item(docstring):
    """
    Parses the given docstring list to print out each line item
    """
    for lineitem in docstring:
        print lineitem

if __name__ == "__main__":
    main()
