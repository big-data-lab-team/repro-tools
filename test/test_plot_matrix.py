import pytest
import subprocess


def test_run():
    command_line = ("plot_matrix test/predict_test/"
                    "test_differences.txt -t test/predict_test/tr"
                    "iangular-S_0.6_test_data_matrix.txt "
                    "test_plot_matrix.png")
    process = subprocess.Popen(command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    code = process.wait()
    print(process.stdout.read().decode("utf-8"))
    print(process.stderr.read().decode("utf-8"))
    assert(not code), "Command failed"
