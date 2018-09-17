import os
import pytest
import subprocess
import filecmp

from reprotools.verify_files import get_dir_dict, read_metrics_file
from reprotools.verify_files import checksum
from reprotools.verify_files import read_file_contents
from reprotools.verify_files import get_conditions_dict
from reprotools.verify_files import get_conditions_checksum_dict


# @pytest.mark.skip(reason="Files produced currently do not match")
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


def test_run_verify_files():
    command_line_string = ("verify_files test/conditions.txt "
                           "results.json -e"
                           " test/exclude_items.txt")
    process = subprocess.Popen(command_line_string,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    code = process.wait()
    print(process.stdout.read().decode("utf-8"))
    print(process.stderr.read().decode("utf-8"))
    assert(code == 0), "Command failed"
    import json
    out = json.loads(open('results.json').read())
    ref_out = json.loads(open('test/differences-ref.json').read())
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


def test_read_metrics():
    metrics = read_metrics_file("test/metrics-list.csv")
    assert metrics["Filter Text"]["output_file"] == "test/filter.csv"
