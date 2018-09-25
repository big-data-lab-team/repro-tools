import pytest
import subprocess
import random
import sys
from reprotools.predict import main as predict
from reprotools import __file__ as repo_init_file_path
import os
from os import path as op


def repopath():
    return op.dirname(repo_init_file_path)

#  shuffled_subject = [1,4,2,0,3]
def test_run():
    os.chdir(op.join(repopath(), 'test', 'predict_test'))
    predict(["test_differences.txt",
             "0.6",
             "ALS",
             "blah",
             "RFNT-S",
             "--seed_number",
             "3"])
