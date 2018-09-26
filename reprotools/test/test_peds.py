import pytest
import subprocess
import os
import json
from reprotools.peds import main as peds
from reprotools.auto_peds import main as auto_peds
from reprotools.verify_files import main as verify_files
from reprotools import __file__ as repo_init_file_path
from os import path as op
from os.path import join as opj


def repopath():
    return op.dirname(repo_init_file_path)


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
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    peds(["trace_test.sqlite3",
          "ref_diff_file.json",
          "-i", "toremove.txt",
          "-g", "graph.dot",
          "-o", "commands.json",
          "-c"])
    assert(open("graph.dot", "r").read() == open("graph_test.dot", "r").read())


def test_capture_first_cond():
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    auto_peds([".",
               "-c", "conditions.txt",
               "-r", ".",
               "-s", "trace_test.sqlite3",
               "-o", "commands.json",
               "-m",
               "-p", "first",
               "-d", "descriptor.json",
               "-i", "invocation.json",
               "-d2", "descriptor_cond2.json",
               "-i2", "invocation_cond2.json"
               ])


def test_capture_second_cond():
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    auto_peds([".",
               "-c", "conditions.txt",
               "-r", ".",
               "-s", "trace_test.sqlite3",
               "-o", "commands.json",
               "-m",
               "-p", "second",
               "-d", "descriptor.json",
               "-i", "invocation.json",
               "-d2", "descriptor_cond2.json",
               "-i2", "invocation_cond2.json"
               ])


def test_verify_files_running():
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    verify_files(["conditions.txt",
                  "test_diff_file.json",
                  "-e", "exclude_items.txt"
                  ])
    out = json.loads(open("test_diff_file.json",
                          "r").read())
    ref_out = json.loads(open("ref_diff_file.json",
                              "r").read())
    comp_json_files(ref_out, out)


def test_auto_peds():
    # ~ test_capture_first_cond()
    # ~ test_capture_second_cond()
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    auto_peds([".",
               "-c", "conditions.txt",
               "-r", ".",
               "-s", "trace_test.sqlite3",
               "-o", "commands.json",
               "-p", "first",
               "-d", "descriptor.json",
               "-i", "invocation.json",
               "-d2", "descriptor_cond2.json",
               "-i2", "invocation_cond2.json"])
    assert(open("commands.json", "r").read()
           == open("result_test.json", "r").read())
