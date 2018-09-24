import pytest
import subprocess
import os
import json


def comp_json_files(ref_out, out):
    for key in ref_out.keys():
        assert(out.get(key))
        assert(out[key]['conditions'] ==
               ref_out[key]['conditions'])
    for f in ref_out[key]['files']:
        assert(out[key]['files'].get(f))
        assert(out[key]['files'][f]['sum']['checksum'] ==
               ref_out[key]['files'][f]['sum']['checksum'])
        for s in ref_out[key]['files'][f]['subjects']:
            assert(out[key]['files'][f]['subjects'].get(s))
            assert(out[key]['files'][f]['subjects'][s]['checksum'] ==
                   ref_out[key]['files'][f]['subjects'][s]['checksum'])


def test_peds():
    command_line = ("peds "
                    "trace_test.sqlite3 "
                    "ref_diff_file.json "
                    "-i toremove.txt "
                    "-g graph.dot "
                    "-o commands.json "
                    "-c true")
    process = subprocess.Popen(command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd='./test/peds_test_data')
    code = process.wait()
    print(process.stdout.read().decode("utf-8"))
    print(process.stderr.read().decode("utf-8"))
    assert(not code), "Command failed"
    assert(open("./test/peds_test_data/graph.dot", "r").read()
           == open("./test/peds_test_data/graph_test.dot", "r").read())


def test_capture_first_cond():
    command = ("auto_peds ./test/peds_test_data "
               "-c ./test/peds_test_data/conditions.txt "
               "-r ./test/peds_test_data "
               "-s ./test/peds_test_data/trace_test.sqlite3 "
               "-o commands.json "
               "-m true "
               "-p first "
               "-d ./test/peds_test_data/descriptor.json "
               "-i ./test/peds_test_data/invocation.json "
               "-d2 ./test/peds_test_data/descriptor_cond2.json "
               "-i2 ./test/peds_test_data/invocation_cond2.json")
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    print(output.decode("utf-8"))
    print(error.decode("utf-8"))


def test_capture_second_cond():
    command = ("auto_peds ./test/peds_test_data "
               "-c ./test/peds_test_data/conditions.txt "
               "-r ./test/peds_test_data "
               "-s ./test/peds_test_data/trace_test.sqlite3 "
               "-o commands.json "
               "-m true "
               "-p second "
               "-d ./test/peds_test_data/descriptor.json "
               "-i ./test/peds_test_data/invocation.json "
               "-d2 ./test/peds_test_data/descriptor_cond2.json "
               "-i2 ./test/peds_test_data/invocation_cond2.json")
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    print(output.decode("utf-8"))
    print(error.decode("utf-8"))


def test_verify_files_running():
    command_line = ("verify_files ./test/peds_test_data/conditions.txt "
                    "./test/peds_test_data/test_diff_file.json "
                    "-e ./test/peds_test_data/exclude_items.txt")
    process = subprocess.Popen(command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,)
    code = process.wait()
    print(process.stdout.read().decode("utf-8"))
    print(process.stderr.read().decode("utf-8"))
    assert(not code), "Command failed"
    out = json.loads(open("./test/peds_test_data/test_diff_file.json",
                          "r").read())
    ref_out = json.loads(open("./test/peds_test_data/ref_diff_file.json",
                              "r").read())
    comp_json_files(ref_out, out)


def test_auto_peds():
    command = ("auto_peds ./test/peds_test_data "
               "-c ./test/peds_test_data/conditions.txt "
               "-r ./test/peds_test_data "
               "-s ./test/peds_test_data/trace_test.sqlite3 "
               "-o commands.json "
               "-m false "
               "-p first "
               "-d ./test/peds_test_data/descriptor.json "
               "-i ./test/peds_test_data/invocation.json "
               "-d2 ./test/peds_test_data/descriptor_cond2.json "
               "-i2 ./test/peds_test_data/invocation_cond2.json")
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    print(output.decode("utf-8"))
    print(error.decode("utf-8"))
    assert(not process.returncode), "Command failed"
    assert(open("./test/peds_test_data/commands.json", "r").read()
           == open("./test/peds_test_data/result_test.json", "r").read())
