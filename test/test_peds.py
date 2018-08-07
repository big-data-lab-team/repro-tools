import pytest
import subprocess
import os


def test_peds():
    command_line = ("peds "
                    "trace.sqlite3 "
                    "test1_differences_subject_total.txt "
                    "-i toremove.txt "
                    "-g graph.dot "
                    "-o commands.json")
    process = subprocess.Popen(command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd='./test/peds_test_data')
    code = process.wait()
    print(process.stdout.read())
    print(process.stderr.read())
    assert(not code), "Command failed"
    assert(open("./test/peds_test_data/graph.dot", "r").read()
           == open("./test/peds_test_data/graph_test1.dot", "r").read())


def test_auto_peds():
    command = ("auto_peds ./test/peds_test_data "
               "-c ./test/peds_test_data/conditions.txt "
               "-r ./test/peds_test_data "
               "-s ./test/peds_test_data/trace.sqlite3 "
               "-o commands.json "
               "-d ./test/peds_test_data/descriptor.json "
               "-i ./test/peds_test_data/invocation.json")
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    print(error)
    assert(not process.returncode), "Command failed"
    assert(open("./test/peds_test_data/commands.json", "r").read()
           == open("./test/peds_test_data/result_test1.json", "r").read())
