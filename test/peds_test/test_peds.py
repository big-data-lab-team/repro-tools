import pytest
import commands
import subprocess, os
   
def test_peds():
    command_line = "python ./reprotools/peds.py -db ./test/peds_test/trace.sqlite3 -ofile ./test/peds_test/error_matrix.txt"
    process = subprocess.Popen(command_line, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    code=process.wait()
    assert(not code), "Command failed"

def test_auto_peds():
    command="python ./reprotools/auto_peds.py"
    process = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output,error = process.communicate()
    if output:
        print "ret> ",process.returncode
        print "OK> output ",output
    if error:
        print "ret> ",process.returncode
        print "Error> error ",error.strip()
    assert(open("./test/peds_test/total_commands.txt","r").read()==open("./test/peds_test/result_modif.txt","r").read())
