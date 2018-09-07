import os
import pytest
import subprocess
import filecmp

from reprotools.verify_files import get_dir_dict, read_metrics_file
from reprotools.verify_files import checksum
from reprotools.verify_files import read_file_contents
from reprotools.verify_files import get_conditions_dict
from reprotools.verify_files import get_conditions_checksum_dict

@pytest.mark.skip(reason="Files produced currently do not match")
def test_checksum():
    assert checksum("test/condition4") == "45a021d9910102aac726dd222a898334"


def test_dir_dict(tmpdir):
    assert get_dir_dict("test/condition4", "test/exclude_items.txt")


def test_conditions_dict():
    conditions_dict = get_mock_conditions_dict()
    assert(conditions_dict['condition4'].keys() ==
           conditions_dict['condition5'].keys())


def get_mock_conditions_dict():
    conditions_list = read_file_contents("test/conditions.txt")
    return get_conditions_dict(conditions_list,
                               "test",
                               "test/exclude_items.txt")


def test_conditions_checksum_dict():
    conditions_dict = get_mock_conditions_dict()
    assert(get_conditions_checksum_dict(conditions_dict,
                                        "test",
                                        "checksums-after.txt"))
<<<<<<< HEAD

=======
>>>>>>> 373ae2d4283c39628713b9961a81edd11b4e3d08
@pytest.mark.skip(reason="Files produced currently do not match")
def test_run_verify_files():
    command_line_string = ("verify_files test/conditions.txt "
                           "fileDiff  results -c checksums-after.txt -e"
                           " test/exclude_items.txt")
    process = subprocess.Popen(command_line_string,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    code = process.wait()
    print(process.stdout.read().decode("utf-8"))
    print(process.stderr.read().decode("utf-8"))
    assert(code == 0), "Command failed"
    assert filecmp.cmp("results/fileDiff_differences_subject_total.txt",
                       "test/differences-ref.txt") 


def test_read_metrics():
    metrics = read_metrics_file("test/metrics-list.csv")
    assert metrics["Filter Text"]["output_file"] == "test/filter.csv"
