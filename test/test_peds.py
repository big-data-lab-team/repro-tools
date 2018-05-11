import pytest
import commands
import subprocess
import os


def test_peds():
    command_line = ("peds "
                    "-d ./test/peds_test_data/trace.sqlite3 "
                    "-m ./test/peds_test_data/error_matrix.txt")
    process = subprocess.Popen(command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    code = process.wait()
    print(process.stdout.read())
    print(process.stderr.read())
    assert(not code), "Command failed"


def test_auto_peds():
    command = ("auto_peds -p ./test/peds_test_data/centos7/test/test_script.sh"
               " -i ./test/peds_test_data/centos7/test/input_file.txt "
               " -o ./test/peds_test_data/centos7/test "
               "-c ./test/peds_test_data/conditions.txt "
               "-r ./test/peds_test_data "
               "-s ./test/peds_test_data/trace.sqlite3")
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    print(error)
    assert(not process.returncode), "Command failed"
    assert(open("./test/peds_test_data/total_commands.txt", "r").read()
           == open("./test/peds_test_data/result_modif.txt", "r").read())
