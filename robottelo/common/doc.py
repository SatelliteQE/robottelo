# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
DocString manipulation methods to create test reports
"""

import ast
import os
import sys

from robottelo.common.constants import CLI_TESTS, DOCSTRING_TAGS, UI_TESTS, \
    REPORT_TAGS
from robottelo.common.helpers import get_root_path

bugs = 0
bug_list = []
invalid_doc_string = 0
manual_count = 0
no_doc_string = 0
tc_count = 0
userinput = None


def main():
    """
    Main function to trigger the reporting functions
    print - Print all test cases
    summary - Summary of number of automated cases vs. manual cases
    validate_docstring - validate docstrings
    bugs - Test cases affected by Bugs and the Bug list
    manual - List all manual test cases
    auto - List all auto test cases

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
    # python robottelo/common/doc.py print

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

    # python robottelo/common/doc.py summary

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

    # python robottelo/common/doc.py validate_docstring

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Analyzing test_sample.py...
    -->Invalid DocString: Creates new domain and delete it<--
    -->Invalid DocString: Create new domain and update its name, description<--
    -->Invalid DocString: Set domain parameter<--
    -->Invalid DocString: Remove selected domain parameter<--
    Total Number of invalid docstrings:  4

    # python robottelo/common/doc.py bugs

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Analyzing test_sample.py...
    Total Number of test cases affected by bugs: 1
    List of bugs:                                ['#1234567']

    python robottelo/common/doc.py manual

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

    # python robottelo/common/doc.py auto

    TEST PATH: /home/framework/robottelo/tests/ui/
    ----------------------------------------------------------------
    Analyzing test_sample.py...
    Creates new domain and deletes it
    Create new domain and update its name, description
    Set domain parameter
    Remove selected domain parameter

    # python robottelo/common/doc.py
    Please enter a valid option to proceed:
    print
    summary
    validate_docstring
    bugs
    manual
    auto

    # python robottelo/common/doc.py invalid
    Please enter a valid option to proceed:
    print
    summary
    validate_docstring
    bugs
    manual
    auto
    """
    global bug_list
    global bugs
    global invalid_doc_string
    global userinput

    #Accept only one paramter.  Error out if argv is < 2 or > 2
    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print_user_message()
    elif not any(x in sys.argv[1] for x in REPORT_TAGS):
        #Error out if user enters a wrong option
        print_user_message()
    userinput = sys.argv[1]
    for input_path in (UI_TESTS, CLI_TESTS):
        reset_counts()
        path = get_root_path() + input_path
        print "\nTEST PATH: %s" % path
        print "--------------------------------------------------------------"
        for root, dirs, files in os.walk(path):
            for i in range(1, len(files)):  # Loop for each file
                if str(files[i]).startswith('test_') and str(files[i]).endswith('.py'):  # @IgnorePep8
                    #Do not print this text for test summary
                    if userinput != REPORT_TAGS[1]:
                        print "Analyzing %s..." % files[i]
                    filepath = path + files[i]
                    list_strings = get_docstrings(filepath)
                    if userinput in REPORT_TAGS[0:3]:
                        #print the derived test cases
                        print_testcases(list_strings)
                    elif userinput == REPORT_TAGS[4]:
                        #print manual test cases
                        print_testcases(list_strings, test_type="manual")
                    elif userinput == REPORT_TAGS[5]:
                        #print auto test cases
                        print_testcases(list_strings, test_type="auto")
                    else:
                        #for printing test summary later
                        update_summary(list_strings)
        #Print for test summary
        if userinput == REPORT_TAGS[1]:
            print_summary()
        #Print total number of invalid doc strings
        if userinput == REPORT_TAGS[2]:
            print "Total Number of invalid docstrings:  %d" % invalid_doc_string  # @IgnorePep8
        #Print number of test cases affected by bugs and also the list of bugs
        if userinput == REPORT_TAGS[3]:
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
    #The body field inside obj.body[] contains the docstring
    #So first find the body field of obj.body[] array
    for i in range(0, len(obj.body)):
        parameters = obj.body[i]._fields
        for attr in parameters:
            if attr == 'body':
                break
    #Now iterate the found body[] list from obj.body[] to find the docstrings
    #Remember that this body[] list will have all different items like class
    #docstrings and functions. So first find the items which are functions
    for j in range(0, len(obj.body[i].body)):
        try:
            obj_param = obj.body[i].body[j]._fields
            for attr in obj_param:
                #Retrieve the func name to check if this is a test_* function
                if attr == 'name':
                    func_name = getattr(obj.body[i].body[j], "name")
                    if func_name.startswith('test'):
                        #Find the docstring value of this function
                        #Remove the trailing spaces
                        value = obj.body[i].body[j].body[0].value.s.lstrip()
                        #Split the docstring with @
                        doclines = value.split('@',)
                        item_list = []
                        for attr in doclines:
                            #Remove trailing spaces
                            attr = attr.rstrip()
                            #Remove any new line characters
                            attr = attr.rstrip('\n')
                            if attr != '':
                                if userinput == REPORT_TAGS[2]:
                                    docstring_tag = attr.split(" ", 1)
                                    #Error out invalid docstring
                                    if not any(x in docstring_tag[0] for x in DOCSTRING_TAGS):  # @IgnorePep8
                                        item_list.append("-->Invalid DocString: %s<--" % attr)  # @IgnorePep8
                                        invalid_doc_string = invalid_doc_string + 1  # @IgnorePep8
                                elif userinput == REPORT_TAGS[3]:
                                    #Find the bug from docstring
                                    docstring_tag = attr.split(" ", 1)
                                    if DOCSTRING_TAGS[5] in docstring_tag[0]:
                                        item_list.append(attr)
                                        bugs = bugs + 1
                                        bug_list.append(docstring_tag[1])
                                else:
                                    #For printing all test cases
                                    item_list.append(attr)
                        if len(item_list) != 0:
                            return_list.append(item_list)
        except AttributeError:
            if userinput == REPORT_TAGS[0] or userinput == REPORT_TAGS[2]:
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
    global userinput
    tc = 0
    for docstring in list_strings:
        if userinput == REPORT_TAGS[0]:
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
        if userinput == REPORT_TAGS[0] or userinput == REPORT_TAGS[2]:
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


def print_user_message():
    """
    Prints all the options for the reporting module
    """
    print "Please enter a valid option to proceed:"
    for attr in REPORT_TAGS:
        print attr
    exit()

if __name__ == "__main__":
    main()
