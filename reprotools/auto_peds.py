#!/usr/bin/python

import argparse
import subprocess
import sys
import fileinput
import csv
import re
import os.path

#Pre-processing: after preparing the result of first condition (CentOS6)
#and getting the processes tree of pipeline using reprozip (db_sqlite), 
#we will detect the pipeline errors and the modify them in the following steps:
#(1) Running pipeline on the other condition (Centos7) to get the results
#(2) Running verify_files.py with results of two conditions to get the matrix file
#(3) Running 'peds.py' script based on the matrix file and db_sqlite 
#    to get a command_line list include all the claddified process
#(4) Modification step to fix the detected processes with error artificially
#(5) if command_line list is empty: break; else go step (1)"


#Modification Step: In order to make appropriate file copy to fix processes artificially, 
#first, we replace the current script with the main pipeline process that create errors.
#after that, script will make a copy of file if arguments are the same with backup command-lines.

# INITIALIZATION
## set env: export reprotool=${PWD}
## set env: export pedsfolder=${PWD}/test/peds_test

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

def replace_script(line, WD, WD_test):
    commands = str(line).split('##')[:1]
    pipe_com = str(commands[0].replace('\x00' or ' ',' '))
    pipeline_commad = pipe_com.split(' ')
    pipe_cmd = pipeline_commad[0].split('/')[-1:][0]
         # check the backup folder and then make cope from input_arg_cmd to that folder if doesn't exist
    backup_path = WD_test+'/backup_scripts/'+str(pipe_cmd)
    if os.path.exists(backup_path)==False:
        bash_command = "cp " + str(which(pipeline_commad[0])) +" "+ backup_path
        os.system(bash_command)
        bash_command = "sudo cp " + WD+"/reprotools/make_copy.py " + str(which(pipeline_commad[0]))
        print(bash_command)
        os.system(bash_command)
   ## instead of second copy make an alias : alias str(pipe_cmd)=$WD/reprotools/make_copy.py updated.txt common.txt"
       # bash_command = "alias " + str(pipe_cmd)+"='python "+WD+"/reprotools/make_copy.py'"
       # print(bash_command)
#        subprocess.Popen(bash_command, shell=True)


def main(args=None):

    WD = os.environ['reprotool']
    WD_test = os.environ['pedsfolder']
    pipeline_script = sys.argv[1]
    input_file = sys.argv[2]
    output_folder = sys.argv[3]
    print(pipeline_script)
    print(output_folder)
    print(input_file)

# Start Modification Loop
    while True :
#(1) Start the Pipeline execution
        pipeline_command = "(cd "+output_folder+"; sh "+pipeline_script+" "+input_file+")"
        os.system(pipeline_command)
#(2) Start to create the error matrix file
        verify_command = WD+'/reprotools/verifyFiles.py '+ WD_test+'/conditions.txt test '+WD_test+'/result'
        os.system(verify_command)
        command = "awk '{print $1,$2}' "+ WD_test+"/result/test_differences_subject_total.txt | tail -n +2 >"+WD_test+"/error_matrix.txt"
        os.system(command)

#(3) Start the classification
        peds_command = "(cd "+WD_test+"; "+WD+'/reprotools/peds.py -db '+ WD_test+'/trace.sqlite3 -ofile '+WD_test+'/error_matrix.txt)'
        os.system(peds_command)

#(4) Start the modification
        if os.stat(WD_test+'/command_lines.txt').st_size>0:
            with open(WD_test+'/command_lines.txt', 'r') as cfile:
                lines = cfile.readlines()
                for line in lines:
                    replace_script(line, WD, WD_test)
        else: break

if __name__ == '__main__':
      main()
