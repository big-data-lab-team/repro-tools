import pytest
import subprocess


def test_run():
    command_line = ("python plot_matrix.py test/predict_test/"
                    "test_differences.txt -t test/predict_test/tr"
                    "iangular-S_0.6_test_data_matrix.txt "
                    "test_plot_matrix.png")
    process = subprocess.Popen(command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    code = process.wait()
    print(process.stdout.read())
    print(process.stderr.read())
    assert(not code), "Command failed"
