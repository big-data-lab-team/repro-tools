from reprotools.diff_file_size import main as diff_file_size
from reprotools import __file__ as repo_init_file_path
import os
from os import path as op


def repopath():
    return op.dirname(repo_init_file_path)


def test_run():
    os.chdir(op.join(repopath(), 'test'))
    assert(diff_file_size(["a/a.txt", "b/a.txt"]) == 0)