import pytest
import subprocess
from reprotools.plot_matrix import main as plot_matrix
from reprotools import __file__ as repo_init_file_path
import os
from os import path as op


def repopath():
    return op.dirname(repo_init_file_path)


def test_run():
    os.chdir(op.join(repopath(), 'test', 'predict_test'))
    plot_matrix(["test_differences.txt",
                 "-t", "triangular-S_0.6_test_data_matrix.txt",
                 "test_plot_matrix.png"
                 ])
