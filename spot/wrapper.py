#!/usr/bin/python

"""Wrapper Script.

This script is renamed and relocated by the executable process
that we are going to label. This script would check the command line
arguments whenever it triggers and make copy files that are creating
differences. In this way we can pinpoint the origin of differences.
"""

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
import logging
import pipes
from spot import __file__ as spot_path
from spot.verify_files import main as verify_files
from spot.spottool import main as spot


def log_info(message):
    logging.info("INFO: " + message)


# def is_intstring(s):
#     try:
#         float(s)
#         return False
#     except ValueError:
#         return True


# def which(exe=None):
#     """Python clone of POSIX's /usr/bin/which."""
#     if exe:
#         (path, name) = op.split(exe)
#         if os.access(exe, os.X_OK):
#             return exe
#         for path in os.environ.get('PATH').split(os.pathsep):
#             full_path = op.join(path, exe)
#             if os.access(full_path, os.X_OK):
#                 return full_path
#     return None


def convert_to_key(cmd):
    lst = []
    ss = cmd.split(' ')
    for l in ss:
        lst.append(l.split('/')[-1])
    cmd = ' '.join(lst)
    cmd = cmd.strip(' ')
    cmd = re.sub(r"fsl_......_tmp", "fsl_X_tmp", cmd)
    cmd = re.sub(r"......_3T_FieldMap_Magnitude",
                 "X_3T_FieldMap_Magnitude", cmd)
    # if 'fslmaths ' in cmd:
    cmd = re.sub(r"(\b|\s+\-?|^\-?)(\d+|\d*\.\d+)\b", " X", cmd)
    return cmd


def csv_parser(command_dic, subj_name):
    command_parsed = {}
    command_parsed_id = {}
    for cmd, files in command_dic.items():
        fname_list = []
        check = False
        command = str(cmd.replace('\x00', ' '))
        command2 = convert_to_key(command)
        for file in files['files']:
            for ind, file_name in enumerate(file.split('/')):
                if file_name == subj_name:
                    fname_list.append("/".join(file.split('/')[ind+1:]))
                    check = True
                    break
            if not check:
                fname_list.append(file)
        # command_parsed[command.strip(' ')] = fname_list
        command_parsed[command2] = fname_list
        command_parsed_id[command2] = files['id']
    return command_parsed, command_parsed_id


def make_copies(pipe_com, pipe_files, WD_ref, WD_dest, val, original_cp):
    for file in pipe_files:
        if val == 'normal':
            from_path = op.join(WD_ref, file)
            if 'spot_temp/' in file:
                file2 = file.replace('spot_temp/', '')
                To_path = op.join(WD_dest, file2)
            else:
                To_path = op.join(WD_dest, file)

        elif val == 'multi-v':
            hash_object = hashlib.sha1(pipe_com.encode('utf-8'))
            hex_dig_file = hash_object.hexdigest()
            Fname = hex_dig_file + "_" + op.basename(file)

            from_path = op.join(WD_ref, op.join(op.dirname(file), Fname))
            To_path = op.join(WD_dest, file)

        cp_command = original_cp + " " + from_path + " " + To_path
        # print(cp_command)
        log_info("copy commands inside the pipeline script: \n" + cp_command)
        subprocess.Popen(cp_command, shell=True,
                         stderr=subprocess.PIPE)


def persist_temp(pipe_files, WD_ref, WD_dest):
    for file in pipe_files:
        from_path = op.join(WD_ref, file)
        To_path = op.abspath(op.join(WD_dest, file))
        if not op.exists(To_path):
            if not op.exists(op.dirname(To_path)):
                os.makedirs(op.dirname(To_path))

        cp_command = "cp " + from_path + " " + To_path
        log_info("copy commands inside the pipeline script: \n" + cp_command)
        subprocess.Popen(cp_command, shell=True,
                         stderr=subprocess.PIPE)


def capture_multi_version(pipe_com, pipe_files, WD_ref, WD_dest):
    for file in pipe_files:
        from_path = op.join(WD_ref, file)
        hash_object = hashlib.sha1(pipe_com.encode('utf-8'))
        hex_dig_file = hash_object.hexdigest()
        Fname = hex_dig_file + "_" + op.basename(file)

        To_path = op.join(WD_dest, op.join(op.dirname(file), Fname))
        if not op.exists(op.dirname(To_path)):
            os.makedirs(op.dirname(To_path))

        cp_command = "cp " + from_path + " " + To_path
        log_info("copy commands inside the pipeline script: \n" + cp_command)
        subprocess.Popen(cp_command, shell=True,
                         stderr=subprocess.PIPE)


def read_copy_files(process_list, subj_name):
    try:
        with open(process_list, 'r') as cfile:
            data = json.load(cfile)
            if "total_commands" not in data:
                commands = {}
            else:
                command_dic = data["total_commands"]
                commands, command_parsed_id = csv_parser(
                    command_dic, subj_name)
            if "total_commands_multi" not in data:
                mw_cmd = {}
            else:
                multi_write = data["total_commands_multi"]
                mw_cmd, command_parsed_id = csv_parser(multi_write, subj_name)
    except Exception:
        mw_cmd = {}
        commands = {}
    return mw_cmd, commands


def read_captured_files(captured_file, subj_name):
    command_parsed_id = {}
    try:
        with open(captured_file, 'r') as c_file:
            data = json.load(c_file)
            if "total_multi_write_proc" not in data:
                total_multi_cmd = {}
            else:
                command_dic_multi = data["total_multi_write_proc"]
                total_multi_cmd, command_parsed_id = csv_parser(
                    command_dic_multi, subj_name)
    except Exception:
        total_multi_cmd = {}
    return total_multi_cmd, command_parsed_id


def read_to_capture_files(captured_list, subj_name):
    capturing = False
    try:
        with open(captured_list, 'r') as c_file:
            data = json.load(c_file)
            if "total_temp_proc" not in data:
                total_temp_cmd = {}
            else:
                capturing = True
                command_dic_temp = data["total_temp_proc"]
                total_temp_cmd, command_parsed_id = csv_parser(
                    command_dic_temp, subj_name)
            if "total_multi_write_proc" not in data:
                total_multi_cmd = {}
            else:
                capturing = True
                command_dic_multi = data["total_multi_write_proc"]
                total_multi_cmd, command_parsed_id = csv_parser(
                    command_dic_multi, subj_name)
    except Exception:
        total_temp_cmd = {}
        total_multi_cmd = {}
    return capturing, total_temp_cmd, total_multi_cmd


def classify_process(spot_output, verify_condition, exclude_items,
                     sqlite_db, process_list, cmd_key):
    diff_flag = False
    try:
        with open(op.join(spot_output, 'test_diff_file.json'), 'r') as o_file:
            old_diff = json.load(o_file)
    except Exception:
        old_diff = {}
        # lst_old = []
    # (1) Run VerifyFiles script to make diff matrix file
    verify_files([verify_condition,
                  op.join(spot_output, 'test_diff_file.json'),
                  "-e",
                  exclude_items
                  ])
    with open(op.join(spot_output, 'test_diff_file.json'), 'r') as n_file:
        new_diff = json.load(n_file)
    if old_diff != new_diff:
        diff_flag = True
        # (2) Run spot script to label processes
        spot([sqlite_db,
              op.join(spot_output, 'test_diff_file.json'),
              "-o", process_list,
              "-i", exclude_items,
              "-a", cmd_key
              ])
    return diff_flag


def copy_files(from_dir, to_dir, single_cmd, mw_cmd, cmd_key, original_cp):
    """Capture single write files with differences."""
    check = False
    from_dir_multi = op.join(from_dir, "multi_version")

    if cmd_key in single_cmd.keys():
        check = True
        make_copies(cmd_key, single_cmd[cmd_key], from_dir,
                    to_dir, 'normal', original_cp)
    if cmd_key in mw_cmd.keys():
        # if cmd_key.split(' ')[0] == 'cp':
        #     continue
        check = True
        make_copies(cmd_key, mw_cmd[cmd_key], from_dir_multi,
                    to_dir, 'multi-v', original_cp)
    return check


def replace_multi_write_file(from_dir, to_dir, mw_cmd, cmd_key, original_cp):
    """Replace..."""
    check = False
    from_dir_multi = op.join(from_dir, "multi_version")
    if cmd_key in mw_cmd.keys():
        check = True
        make_copies(cmd_key, mw_cmd[cmd_key], from_dir_multi,
                    to_dir, 'multi-v', original_cp)
    return check


def capture_files(subject_dir1, total_temp_commands,
                  total_multi_commands, input_arg_cmd):
    """Capture intermediate files with differences."""
    to_temp = op.join(subject_dir1, "spot_temp")
    to_multi = op.join(subject_dir1, "multi_version")

    # Capture the temporary files
    if input_arg_cmd in total_temp_commands.keys():
        persist_temp(total_temp_commands[input_arg_cmd], subject_dir1, to_temp)

    # Capture multi-write processes error
    if input_arg_cmd in total_multi_commands.keys():
        capture_multi_version(input_arg_cmd,
                              total_multi_commands[input_arg_cmd],
                              subject_dir1, to_multi)


def add_to_ignored_multi(cmd_id, process_list):
    with open(process_list, 'r') as rfile:
        data = json.load(rfile)
    data["ignored_multi"].append(cmd_id)
    with open(process_list, 'w+') as json_file:
        json.dump(data, json_file, indent=4, sort_keys=True)


def main(args=None):
    spot_path = os.getenv('SPOT_TOOLS_PATH')
    assert(spot_path), 'SPOT_TOOLS_PATH is not defined'
    spot_output = os.getenv('SPOT_OUTPUT_PATH')
    from_path = os.getenv("FROM_PATH")
    to_path = os.getenv("TO_PATH")
    process_list = os.getenv("PROCESS_LIST")
    logging.basicConfig(filename=op.join(spot_output, 'spot_commands.log'),
                        format='%(asctime)s:%(message)s', level=logging.INFO)
    OS_release = platform.linux_distribution()[1]
    original_cp = op.join(spot_output, 'backup_scripts/usr/bin/cp')
    current_script_name = __file__
    cmd_name = current_script_name.split('/')[-1:][0]
    command = op.join(spot_output, 'backup_scripts',
                      current_script_name.strip("/"))
    if not op.exists(command):
        command = op.join(spot_output, 'backup_scripts', cmd_name)

    cmdline = " ".join(map(pipes.quote, sys.argv[1:]))
    command = command + " " + cmdline
    # command = command + " " + " ".join(sys.argv[1:])

    with open(process_list, 'r') as read_info:
        info_ = json.load(read_info)
    subj_name = info_["execution_info"]["subject_name"]
    verify_condition = info_["execution_info"]["conditions"]
    exclude_items = info_["execution_info"]["exclude_items"]
    sqlite_db = info_["execution_info"]["sqlite_db"]
    captured_list = info_["execution_info"]["captured_list"]

    if cmd_name != 'wrapper':
        capturing, total_temp_cmd, total_multi_cmd = \
                                read_to_capture_files(captured_list, subj_name)

        cmd_key = convert_to_key(command)
        # Execute invoked process
        subprocess.Popen(command, shell=True).communicate()
        msg = "OS_RELEASE: " + str(OS_release) + \
              "\ncommand executed: " + command
        log_info(msg)
        if capturing:
            log_info("capturing is TRUE")
            capture_files(from_path, total_temp_cmd, total_multi_cmd, cmd_key)

        else:
            # Labelling the processs:
            total_multi_cmd, command_parsed_id = read_captured_files(
                captured_list.replace('.json', '_c.json'), subj_name)
            cp_flag = replace_multi_write_file(
                          from_path, from_path, total_multi_cmd, cmd_key,
                          original_cp)
            if cp_flag or (cmd_name != 'cp'):
                check = classify_process(spot_output, verify_condition,
                                         exclude_items, sqlite_db,
                                         process_list, cmd_key)
                ignore = False
                if check is True:
                    mw_cmd, single_cmd = read_copy_files(
                                             process_list, subj_name)
                    # MAKE COPY
                    ignore = copy_files(
                                 from_path, to_path, single_cmd, mw_cmd,
                                 cmd_key, original_cp)
                if cp_flag and (not ignore):
                    add_to_ignored_multi(
                        command_parsed_id[cmd_key], process_list)


if __name__ == '__main__':
    main()
