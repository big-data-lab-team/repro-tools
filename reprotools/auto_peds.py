#!/usr/bin/python

import argparse
import subprocess
import sys
import fileinput
import csv
import re
import os.path
from shutil import copyfile

# Pre-processing: after preparing the result of first condition (CentOS6)
# and getting the processes tree of pipeline using reprozip (db_sqlite),
# we detect the pipeline errors and the modify them in the following steps:
# (1) Running pipeline on the other condition (Centos7) to get the results
# (2) Running verify_files.py with results of two conditions to get the
# matrix file
# (3) Running 'peds.py' script based on the matrix file and db_sqlite
#    to get a command_line list include all the claddified process
# (4) Modification step to fix the detected processes with error artificially
# (5) if command_line list is empty: break; else go step (1)"


def which(exe=None):
    '''
    Python clone of POSIX's /usr/bin/which
    '''
    if exe:
        (path, name) = os.path.split(exe)
        if os.access(exe, os.X_OK):
            return exe
        for path in os.environ.get('PATH').split(os.pathsep):
            full_path = os.path.join(path, exe)
            if os.access(full_path, os.X_OK):
                return full_path
    return None


def bash_executor(execution_dir, command):
    process = subprocess.Popen(command,
                               shell=True,
                               stderr=subprocess.PIPE,
                               cwd=execution_dir)
    output, error = process.communicate()
    if(process.returncode):
        if output:
            print(output)
        if error:
            print(error)
        raise Exception("Pipeline execution failed")


def replace_script(line, peds_data_path):
    commands = str(line).split('##')[:1]
    pipeline_command = commands[0].replace('\x00', ' ').split(' ')[0]
    # Make a copy of process to backup folder if doesn't exist
    backup_path = os.path.join(peds_data_path, 'backup_scripts', pipeline_command)
    if not os.path.exists(backup_path):
        if not os.path.exists(os.path.dirname(backup_path)):
            os.makedirs(os.path.dirname(backup_path))
        copyfile(which(pipeline_command), backup_path)
        copyfile(os.path.join(os.path.dirname(__file__), 'make_copy.py'), which(pipeline_command))

def main(args=None):
    # Use argparse
    parser = argparse.ArgumentParser(description='Automation of pipeline error detection')
    parser.add_argument("output_directory", help="directory where to store the output")
    parser.add_argument("-p", "--pipe_exec",
                        help="executions file of the pipeline")
    parser.add_argument("-i", "--pipe_input",
                        help="input data of pipeline running")
    parser.add_argument("-o", "--pipe_output",
                        help="path of pipeline output directory")
    parser.add_argument("-c", "--verify_condition",
                        help="input the text file containing the path to the verify_file condition folders")
    parser.add_argument("-r", "--verify_output",
                        help="path of verify_file outputs")
    parser.add_argument("-s", "--sqlite_db",
                        help="sqlite file created by reprozip")

    args = parser.parse_args()
    peds_data_path = os.path.abspath(args.output_directory)
    pipe_exec = os.path.abspath(args.pipe_exec)
    pipe_input = os.path.abspath(args.pipe_input)
    pipe_output = os.path.abspath(args.pipe_output)
    verify_cond = args.verify_condition
    verify_output = args.verify_output
    sqlite_db = os.path.abspath(args.sqlite_db)
    first_iter = True
# Start Modification Loop
    while True:

        # (1) Start the Pipeline execution
        pipeline_command = pipe_exec+" "+pipe_input
        bash_executor(pipe_output, pipeline_command)

        # (2) Start to create the error matrix file
        verify_command = 'verify_files ' + verify_cond + ' test ' + verify_output
        bash_executor(os.getcwd(), verify_command)

        with open(os.path.join(verify_output, 'test_differences_subject_total.txt'), 'r') as mfile:
            lines = mfile.readlines()
        sample = ""
        for line in lines[1:]:
            splitedLine = line.split('\t')
            sample += (splitedLine[0].replace(' ', '') + " " + str(int(splitedLine[1]))+"\n")
        write_matrix = open(os.path.join(peds_data_path, 'error_matrix.txt'), 'w')
        write_matrix.write(sample)
        write_matrix.close()

        # (3) Start the classification
#        if first_iter is True:
#            os.remove(os.path.join(peds_data_path, 'total_commands.txt'))
#            first_iter = False
        peds_command = "peds -d " + sqlite_db + " -m error_matrix.txt"
        bash_executor(peds_data_path, peds_command)

        # (4) Start the modification
        if os.stat(os.path.join(peds_data_path, 'command_lines.txt')).st_size > 0:
            with open(os.path.join(peds_data_path, 'command_lines.txt'), 'r') as cfile:
                lines = cfile.readlines()
                for line in lines:
                    replace_script(line, peds_data_path)
        else: break


if __name__ == '__main__':
    main()
