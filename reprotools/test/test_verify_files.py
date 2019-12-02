import os
import pytest
import subprocess
import filecmp
import json

import os.path as op

from reprotools.verify_files import get_dir_dict, read_metrics_file
from reprotools.verify_files import checksum
from reprotools.verify_files import read_file_contents
from reprotools.verify_files import get_conditions_dict
from reprotools.verify_files import get_conditions_checksum_dict
from reprotools.verify_files import main as verify_files
from reprotools import __file__ as base_file


def repopath(file_path):
    return op.join(op.dirname(base_file), file_path)


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


# @pytest.mark.skip(reason="Files produced currently do not match")
def test_checksum():
    os.chdir(op.dirname(base_file))
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


def test_run_verify_files():
    os.chdir(op.dirname(base_file))
    try:
        verify_files([repopath("test/conditions.txt"),
                      "results.json",
                      "-e",
                      repopath("test/exclude_items.txt")])
    except Exception as e:
        pytest.fail('Unexpected error')
    out = json.loads(open('results.json').read())
    ref_out = json.loads(open(repopath('test/differences-ref.json')).read())
    # comp_json_files(ref_out, out)


def test_read_metrics():
    metrics = read_metrics_file(repopath("test/metrics-list.csv"))
    assert metrics["Filter Text"]["output_file"] == "test/filter.csv"
