import pytest
import commands
import subprocess
import os


def test_peds():
    command_line = ("peds"
                    "-d ./test/peds_test_data/trace.sqlite3"
                    "-m ./test/peds_test_data/error_matrix.txt")
    process = subprocess.Popen(command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    code = process.wait()
    assert(not code), "Command failed"


def test_auto_peds():
    command = ("auto_peds test_script.sh "
               "input_file.txt ./test/peds_test_data/centos7/test/")
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    if output:
        print("ret> ", process.returncode)
        print("OK> output ", output)
    if error:
        print("ret> ", process.returncode)
        print("Error> error ", error.strip())
    assert(open("./test/peds_test_data/total_commands.txt", "r").read()
           == open("./test/peds_test_data/result_modif.txt", "r").read())
