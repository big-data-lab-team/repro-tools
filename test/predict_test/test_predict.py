import pytest
import subprocess
import random
import sys


#  shuffled_subject = [1,4,2,0,3]
def test_run():
    command_line_string = ("python predict.py test/predict_test/test_"
                           "differences.txt 0.6 triangular-S -s 3")
    process = subprocess.Popen(command_line_string,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    code = process.wait()
    print(process.stdout.read())
    print(process.stderr.read())
    assert(code == 0), "Command failed"
