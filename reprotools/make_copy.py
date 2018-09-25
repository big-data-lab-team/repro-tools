#!/usr/bin/python

import subprocess
import sys
import fileinput
import csv
import re
import os
import json
import os.path as op
from shutil import copyfile
import platform
import hashlib

# Modification Step: In order to make appropriate file copy to
# fix processes artificially, first, we replace the current script with
# the main pipeline process that create errors. after that, script will
# make a copy of file if arguments are the same with backup command-lines.


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


def csv_parser(command_dic):
    command_parsed = {}
    for cmd, files in command_dic.items():
        fname_list = []
        # ~ command = str(line).split('##')[:1]
        # ~ command = str(command[0].replace('\x00', ' '))
        command = str(cmd.replace('\x00', ' '))
        for file in files:
            count = 0
            for f in file.split('/'):
                # if f == "exec":
                if f == "subject1":
                    count += 1
                    break
                else:
                    count += 1
            fname_list.append("/".join(file.split('/')[count:]))
        command_parsed[command] = fname_list
    return command_parsed


def check_arguments(pipe_com, input_arg_cmd):
    check = False
    pipeline_commad = pipe_com.split(' ')
    if which(pipeline_commad[0]) == which(input_arg_cmd):
        if len(pipeline_commad)-1 == len(sys.argv):
            check = True
            i = 1
            while i < len(sys.argv):
                if (op.basename(pipeline_commad[i]) !=
                        op.basename(sys.argv[i]) and
                        is_intstring(sys.argv[i])):
                    check = False
                    break
                i += 1
    return check


def make_copies(pipe_com, pipe_files, WD_ref, WD_dest, val):
    proc_name = op.basename(pipe_com.split(' ')[0])
    for file in pipe_files:
        from_path = op.join(WD_ref, file)
        # ~ Fname = proc_name + "_" + file
        hash_object = hashlib.sha1(pipe_com.encode('utf-8'))
        hex_dig_file = hash_object.hexdigest()
        Fname = hex_dig_file + "_" + file
        if val == 'normal':
            if 'peds_temp/' in file:
                file2 = file.replace('peds_temp/', '')
                Fname2 = hex_dig_file + "_" + file2
                from_path = op.join(WD_ref, op.join('peds_temp', Fname2))
                To_path = op.join(WD_dest, file2)
                cp_command2 = "cp " + from_path + " " + To_path
                subprocess.Popen(cp_command2, shell=True,
                                 stderr=subprocess.PIPE)
                To_path = op.join(WD_dest, op.join('peds_temp', Fname2))
            else:
                To_path = op.join(WD_dest, file)

        elif val == 'multi-v':
            from_path = op.join(WD_ref, op.join('multi_version', Fname))
            To_path = op.join(WD_dest, file)
        elif val == 'persist':
            To_path = op.join(WD_dest, Fname)
            # ~ while op.exists(To_path):
            # ~ Fname = proc_name + "_" + Fname
            # ~ To_path = op.join(WD_dest, Fname)
        cp_command = "cp " + from_path + " " + To_path
        subprocess.Popen(cp_command, shell=True,
                         stderr=subprocess.PIPE)


def read_files(WD_test):
    try:
        with open(op.join(WD_test, 'commands.json'), 'r') as cfile:
            data = json.load(cfile)
            if "total_commands" not in data:
                commands = {}
            else:
                command_dic = data["total_commands"]
                commands = csv_parser(command_dic)
            if "total_commands_multi" not in data:
                mw_cmd = {}
            else:
                multi_write = data["total_commands_multi"]
                mw_cmd = csv_parser(multi_write)
    except Exception:
        mw_cmd = {}
        commands = {}

    try:
        with open(op.join(WD_test, 'commands_captured.json'), 'r') as c_file:
            data = json.load(c_file)
            if "total_temp_proc" not in data:
                total_temp_commands = {}
            else:
                command_dic_temp = data["total_temp_proc"]
                total_temp_commands = csv_parser(command_dic_temp)
            if "total_multi_write_proc" not in data:
                total_multi_commands_commands = {}
            else:
                command_dic_multi = data["total_multi_write_proc"]
                total_multi_commands_commands = csv_parser(command_dic_multi)
    except Exception:
        total_temp_commands = {}
        total_multi_commands_commands = {}

    return mw_cmd, commands, total_temp_commands, total_multi_commands_commands


def main(args=None):

    repro_path = os.getenv('REPRO_TOOLS_PATH')
    assert(repro_path), 'REPRO_TOOLS_PATH is not defined'
    WD_test = op.join(repro_path, 'test/peds_test_data')
    # single_cmd  refer to the single processes that create errors
    # mw_cmd refers to the multi-write processes that create errors
    mw_cmd, single_cmd, total_temp_commands, total_multi_commands = (
                                                    read_files(WD_test))

    OS_release = platform.linux_distribution()[1]
    input_arg_cmd = sys.argv[0]
    current_script_name = __file__
    cmd_name = current_script_name.split('/')[-1:][0]
    command = op.join(WD_test, 'backup_scripts', str(cmd_name))
    i = 1
    while i < len(sys.argv):
        command += " " + sys.argv[i]
        i += 1
    subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)

# ####### ON FIRST CONDITION (CENTOS7  ######## iteratively
    # Capture single write error files
    WD_ref = op.join(WD_test, "centos6/subject1")
    WD_cur = op.join(WD_test, "centos7/subject1")

    for pipe_com, pipe_files in single_cmd.items():
        check = check_arguments(pipe_com, input_arg_cmd)
        if check is True:
            make_copies(pipe_com, pipe_files, WD_ref, WD_cur, 'normal')
            break

    # Capture multi-write processes error
    for pipe_com2, pipe_files2 in mw_cmd.items():
        check2 = check_arguments(pipe_com2, input_arg_cmd)
        if check2 is True:
            make_copies(pipe_com2, pipe_files2, WD_ref, WD_cur, 'multi-v')
            break

# ####### ON FIRST (CENTOS7) AND REF(CENTOS6) CONDITIONS  ######## one time
    if OS_release == "7.5.1804":
        WD_temp = op.join(WD_test, "centos7/subject1")
        WD_temp_persist = op.join(WD_test, "centos7/subject1/peds_temp")
        WD_multi = op.join(WD_test, "centos7/subject1")
        WD_multi_persist = op.join(WD_test, "centos7/subject1/multi_version")

    elif OS_release == "6.8":
        WD_temp = op.join(WD_test, "centos6/subject1")
        WD_temp_persist = op.join(WD_test, "centos6/subject1/peds_temp")
        WD_multi = op.join(WD_test, "centos6/subject1")
        WD_multi_persist = op.join(WD_test, "centos6/subject1/multi_version")

    # Capture the temporary files
    for pipe_com3, pipe_files3 in total_temp_commands.items():
        check3 = check_arguments(pipe_com3, input_arg_cmd)
        if check3 is True:
            make_copies(pipe_com3, pipe_files3, WD_temp,
                        WD_temp_persist, 'persist')
            break

    # Capture multi-write processes error
    for pipe_com2, pipe_files2 in total_multi_commands.items():
        check2 = check_arguments(pipe_com2, input_arg_cmd)
        if check2 is True:
            make_copies(pipe_com2, pipe_files2, WD_multi,
                        WD_multi_persist, 'persist')
            break


if __name__ == '__main__':
    main()
