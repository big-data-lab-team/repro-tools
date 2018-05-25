#!/usr/bin/python

import argparse
import subprocess
import sys
import fileinput
import csv
import re
import os
import os.path as op
from reprotools import __file__ as path
from shutil import copyfile

#Modification Step: In order to make appropriate file copy to fix processes artificially, 
#first, we replace the current script with the main pipeline process that create errors.
#after that, script will make a copy of file if arguments are the same with backup command-lines.


def is_intstring(s):
    try:
        float(s)
        return False
    except ValueError:
        return True


def which(exe=None):
    '''
    Python clone of POSIX's /usr/bin/which
    '''
    if exe:
        (path, name) = op.split(exe)
        if os.access(exe, os.X_OK):
            return exe
        for path in os.environ.get('PATH').split(os.pathsep):
            full_path = op.join(path, exe)
            if os.access(full_path, os.X_OK):
                return full_path
    return None


def csv_parser(cfile):
    command_parsed = {}
    for line in cfile:
        fname_list = []
        command = str(line).split('##')[:1]
        command = str(command[0].replace('\x00', ' '))
        file_name = str(line).split('##')[1:]
        flist = file_name[0][2:-3].replace("'", '').split(',')
        for file in flist:
            count = 0
            for f in file.split('/'):
            #  if f == "exec":
                if f == "centos7":
                    count += 1
                    break
                else: count += 1
            fname_list.append("/".join(file.split('/')[count:]))
        command_parsed[command] = fname_list
    return command_parsed


def main(args=None):

    WD_test = op.join(op.dirname(op.abspath(path)), '../test/peds_test_data')
    #WD_test = '/home/ali/Desktop/git_repo/repro-tools/test/peds_test_data'
    # updated commands refer to the single processes that create errors
    # common_cmd refers to the multi-write processes that create errors
    with open(op.join(WD_test, 'total_commands.txt'), 'r') as cfile:
        commands = csv_parser(cfile)
    try:
        with open(op.join(WD_test, 'common_cmd.txt'), 'r')as multi_write_file:
            multi_write_commands = csv_parser(multi_write_file)
    except: multi_write_commands = []
    proc_list = multi_write_commands.keys()

    input_arg_cmd = sys.argv[0]
    current_script_name = __file__
    cmd_name = current_script_name.split('/')[-1:][0]
    command = op.join(WD_test, 'backup_scripts', str(cmd_name))
    i = 1
    while i<len(sys.argv):
        command += " " + sys.argv[i]
        i += 1
    subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)

    WD_ref = op.join(WD_test, "centos6/test")
    WD_cur = op.join(WD_test, "centos7/test")
    # WD_ref_saved = WD_test+"/centos6_common_files/"
    # WD_cur_save = WD_test+"/centos7_common_files/"
    for pipe_com, pipe_files in commands.items():
        check = False
        pipeline_commad = pipe_com.split(' ')
        if which(pipeline_commad[0]) == which(input_arg_cmd):
            if len(pipeline_commad)-1 == len(sys.argv):
                check = True
                i = 1
                while i < len(sys.argv):
                    if pipeline_commad[i] != op.basename(sys.argv[i]) and is_intstring(sys.argv[i]):
                        check = False
                        break
                    i += 1
        if check is True:
            for file in pipe_files:
                from_path = op.join(WD_ref, file)
                To_path = op.join(WD_cur, file)
                cp_command = "cp " + from_path + " " + To_path
                subprocess.Popen(cp_command, shell=True, stderr=subprocess.PIPE)
               # copyfile(from_path, To_path)

                # f_ = file.split('/')[-1]
                # _f = file.split('/')[:-1]
                # if pipe_com in common_list:
                #     proc_fname = str(pipeline_commad[0].split('/')[-1])+"_" #for common file add proc name:  'procname_filename'
                #     #from_common_file = WD_ref + _f + proc_fname + f_
                #     To_common_file = WD_cur + _f + proc_fname + f_ ##
                #    # bash_command = "cp " + from_common_file + " " + To_common_file
                #     bash_command = "cp " + from_path + " " + To_common_file
                #     os.system(bash_command)

                #if pipe_com in temp_list:
                #   # from_temp_file = WD_ref + _f + "temp_" + f_ #for common file add temp:  'temp_filename'
                #    To_temp_file = WD_cur + _f + "temp_" + f_
                #   # bash_command = "cp " + from_temp_file + " " + To_temp_file
                #    bash_command = "cp " + from_path + " " + To_temp_file
                #    os.system(bash_command)
            break
        else: continue


if __name__ == '__main__':
    main()
