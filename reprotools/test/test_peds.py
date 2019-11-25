import subprocess
import os
import json
from reprotools.peds import main as peds
from reprotools.auto_peds import main as auto_peds
from reprotools.make_copy import main as make_copy
from reprotools.subj_clustering import main as subject_clustering
from reprotools.verify_files import main as verify_files
from reprotools import __file__ as repo_init_file_path
from os import path as op
from os.path import join as opj


def repopath():
    return op.dirname(repo_init_file_path)


def test_make_copy():
    peds_data_path = op.join(repopath(), 'test', 'peds_test_data')
    from_path = op.join(op.abspath("centos6"), "subject1")
    to_path = op.join(op.abspath("centos7"), "subject1")
    os.chdir(peds_data_path)
    os.environ["REPRO_TOOLS_PATH"] = os.getcwd()
    os.environ["NURM_OUTPUT_PATH"] = peds_data_path
    os.environ["PROCESS_LIST"] = op.join(peds_data_path, "commands_test.json")
    os.environ["FROM_PATH"] = from_path
    os.environ["TO_PATH"] = to_path
    make_copy()


def test_make_copy_cap():
    peds_data_path = op.join(repopath(), 'test', 'peds_test_data')
    from_path = op.join(op.abspath("centos6"), "subject1")
    to_path = op.join(op.abspath("centos7"), "subject1")
    os.chdir(peds_data_path)
    os.environ["REPRO_TOOLS_PATH"] = os.getcwd()
    os.environ["NURM_OUTPUT_PATH"] = peds_data_path
    os.environ["PROCESS_LIST"] = op.join(peds_data_path, "commands_cap_test.json")
    os.environ["FROM_PATH"] = from_path
    os.environ["TO_PATH"] = to_path
    make_copy()


def test_subj_clustering():
    os.chdir(op.join(repopath(), 'test'))
    subject_clustering(["-p", "true",
          "subject-type-test/in_test_subjects/",
          "subject-type-test/out_test_plots/"])


def test_subj_clustering2():
    os.chdir(op.join(repopath(), 'test'))
    subject_clustering(["-t", "1.0",
          "subject-type-test/in_test_subjects/",
          "subject-type-test/out_test_plots/"])
#     assert(open("subject-type-test/clusters_test.txt", "r").read() 
#            == open("subject-type-test/output-trees/clusters.txt", "r").read())


def test_auto_peds():
    # ~ test_capture_first_cond()
    # ~ test_capture_second_cond()
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    wrapper_script = op.join(repopath(), 'make_copy.py')
    auto_peds([".",
               "-c", "conditions.txt",
               "-e", "exclude_items.txt",
               "-s", "trace_test.sqlite3",
               "-o", "commands.json",
               "-m", "make_copy.py",
               "-d", "descriptor.json",
               "-i", "invocation.json",
               "-d2", "descriptor_cond2.json",
               "-i2", "invocation_cond2.json",
               "-r", "centos6",
               "-b", "centos7"
               ])
#     assert(open("commands.json", "r").read()
#            == open("result_test.json", "r").read())


def test_peds():
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    peds(["trace_test.sqlite3",
          "ref_diff_file.json",
          "-i", "toremove.txt",
          "-o", "commands_test2.json"])
#     assert(open("graph.dot", "r").read() == open("graph_test.dot", "r").read())


def test_peds2():
    os.chdir(op.join(repopath(), 'test', 'peds_test_data'))
    peds(["trace_test.sqlite3",
          "ref_diff_file.json",
          "-i", "toremove.txt",
          "-o", "commands_test2.json",
          "-a", "grep 6.8 input_file.txt"])