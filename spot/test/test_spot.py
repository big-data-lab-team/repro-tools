import subprocess
import os
import json
from spot.spottool import main as spot
from spot.auto_spot import main as auto_spot
from spot.wrapper import main as wrapper
from spot.subj_clustering import main as subject_clustering
from spot.verify_files import main as verify_files
from spot import __file__ as repo_init_file_path
from os import path as op
from os.path import join as opj


def repopath():
    return op.dirname(repo_init_file_path)


def test_wrapper():
    spot_data_path = op.join(repopath(), 'test', 'spot_test_data')
    from_path = op.join(op.abspath("debian"), "subject1")
    to_path = op.join(op.abspath("centos7"), "subject1")
    os.chdir(spot_data_path)
    os.environ["SPOT_TOOLS_PATH"] = os.getcwd()
    os.environ["SPOT_OUTPUT_PATH"] = spot_data_path
    os.environ["PROCESS_LIST"] = op.join(spot_data_path, "commands_test.json")
    os.environ["FROM_PATH"] = from_path
    os.environ["TO_PATH"] = to_path
    wrapper()


def test_wrapper_cap():
    spot_data_path = op.join(repopath(), 'test', 'spot_test_data')
    from_path = op.join(op.abspath("debian"), "subject1")
    to_path = op.join(op.abspath("centos7"), "subject1")
    os.chdir(spot_data_path)
    os.environ["SPOT_TOOLS_PATH"] = os.getcwd()
    os.environ["SPOT_OUTPUT_PATH"] = spot_data_path
    os.environ["PROCESS_LIST"] = op.join(spot_data_path, "commands_cap_test.json")
    os.environ["FROM_PATH"] = from_path
    os.environ["TO_PATH"] = to_path
    wrapper()


def test_subj_clustering2():
    os.chdir(op.join(repopath(), 'test'))
    subject_clustering(["-t", "1.0",
          "subject-type-test/in_test_subjects/",
          "subject-type-test/out_test_plots/"])
#     assert(open("subject-type-test/clusters_test.txt", "r").read() 
#            == open("subject-type-test/output-trees/clusters.txt", "r").read())


def test_auto_spot():
    # ~ test_capture_first_cond()
    # ~ test_capture_second_cond()
    os.chdir(op.join(repopath(), 'test', 'spot_test_data'))
    auto_spot([".",
               "-d", "descriptor.json",
               "-i", "invocation.json",
               "-d2", "descriptor_cond2.json",
               "-i2", "invocation_cond2.json",
               "-c", "conditions.txt",
               "-e", "exclude_items.txt",
               "-s", "trace_test.sqlite3",
               "-o", "commands.json"
               ])
#     assert(open("commands.json", "r").read()
#            == open("result_test.json", "r").read())


def test_spot():
    os.chdir(op.join(repopath(), 'test', 'spot_test_data'))
    spot(["trace_test.sqlite3",
          "ref_diff_file.json",
          "-i", "toremove.txt",
          "-o", "commands_test2.json"])


def test_spot2():
    os.chdir(op.join(repopath(), 'test', 'spot_test_data'))
    spot(["trace_test.sqlite3",
          "ref_diff_file.json",
          "-i", "toremove.txt",
          "-o", "commands_test2.json",
          "-a", "grep 67890 input_file.txt"])