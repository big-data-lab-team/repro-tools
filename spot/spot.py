#!/usr/bin/python

"""Label Pipeline Processes.

This script would label processes based on the file dependency of
the process.
"""

import os
import os.path as op
import re
import argparse
import sqlite3
import json
import logging
import sys
import pandas as pd
from sqlite3 import Error
try:
    import cPickle as pickle
except ImportError:
    import pickle
import time
import pipes


class node_structure:
    """Node structure of the linked list of process."""

    def __init__(self, initdata, pid, parent_id, process_name, level):
        """Initialize node attributes."""
        self.id = pid
        self.name = process_name
        self.pid = parent_id
        self.data = initdata
        self.level = level
        self.next = None


class linked_list:
    """Linked list class of process."""

    def __init__(self):
        self.head = None

    def is_empty(self):
        return (self.head is None)

    # # Returns the size of the list
    # def size(self):
    #     current = self.head
    #     count = 0
    #     while current is not None:
    #         count = count + 1
    #         current = current.next
    #     return count

    # Returns the list of graph nodes
    def to_list(self):
        current = self.head
        result = []
        while current is not None:
            result.append(current)
            current = current.next
        return result

    # Add the new node(process) to list
    def add(self, item, pid, parent_id, process_name, level):
        new_node = node_structure(item, pid, parent_id, process_name, level)
        new_node.next = self.head
        self.head = new_node

    # # Reverse the list which the head of list refer to the root process
    # def reverse(self):
    #     prev = None
    #     current = self.head
    #     while (current is not None):
    #         next = current.next
    #         current.next = prev
    #         prev = current
    #         current = next
    #     self.head = prev
    #     return prev

    # keep the correspond processes in the pipeline
    # and remove the other processes
    def filter(self, exclude_items):
        prev = None
        current = self.head
        level_id = []
        # Restrict depth of tree to search
        level = 15
        while (current is not None):
            next = current.next
            if len(current.data) != 0:
                # keep just the files of its process
                data = current.data
                current.data = ()
                for d in data:
                    if d[0] == current.id:
                        # filter out process data based on exclude input file
                        check = True
                        for item in exclude_items:
                            if item in d[1]:
                                check = False
                                break
                        if check:
                            current.data += (d,)
                if current.data == ():
                    continue
                # identifying the root process (as the main pipeline elements)
                if current.pid[0][0] is None:
                    level_id.append([current.id, 0])
                    current.level = 0
                    # current.next = prev
                    # prev = current
                # here we can expand the final result to
                # more sub-process details instead of first-level
                for line2 in level_id:
                    tmp = current.pid[0]
                    if line2[0] == tmp[0]:
                        if line2[1] < level:
                            level_id.append([current.id, line2[1] + 1])
                            current.level = line2[1] + 1
                            # current.next = prev
                            # prev = current

                current.next = prev
                prev = current
            current = next
        self.head = prev
        return prev

    # Add new data to the process data when the program is aggregated
    def append(self, pid, newfiles):
        current = self.head
        found = False
        while current is not None and not found:
            if current.id == pid:
                current.data += newfiles
                found = True
            else:
                current = current.next

    # Returns the data of process
    def get_data(self, item):
        current = self.head
        found = False
        while current is not None and not found:
            if current.id == item:
                return current.data
            else:
                current = current.next

    # Returns the data of process by name
    def get_data_name(self, item):
        current = self.head
        found = False
        while current is not None and not found:
            if current.name == []:
                current = current.next
                continue
            cmd = str(current.name[0][1].replace('\x00', ' ')).strip(' ')
            cmd = cmd.split(' ')
            cmdline = " ".join(map(pipes.quote, cmd))
            command = convert_to_key(cmdline)
            if command == item:
                return current
            else:
                current = current.next

    # # Remove the process from list
    # def remove(self, item):
    #     current = self.head
    #     previous = None
    #     found = False
    #     while not found:
    #         if current.data == item:
    #             found = True
    #         else:
    #             previous = current
    #             current = current.next
    #     if previous is None:
    #         self.head = current.next
    #     else:
    #         previous.setNext(current.next)

    def get_name(self, item):
        current = self.head
        found = False
        while current is not None and not found:
            if current.id == item:
                return current.name
            else:
                current = current.next


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
#    if 'fslmaths ' in cmd:
    cmd = re.sub(r"(\b|\s+\-?|^\-?)(\d+|\d*\.\d+)\b", " X", cmd)
    return cmd


def create_graph(pid, process_node, db_path):
    """Create the process tree based on the reprozip trace file."""
    try:
        db = sqlite3.connect(db_path)
        # db.text_factory = str
    except Error as e:
        print(e)
    process_cursor = db.cursor()
    openfile_cursor = db.cursor()
    executed_cursor = db.cursor()
    parent_cursor = db.cursor()
    writefile_cursor = db.cursor()

    # select the list of child process of pid
    child_list = get_the_child_processes(process_cursor, pid)
    # select the process name
    process_name = get_the_processes_name(executed_cursor, pid)
    # select the list of opened files (w/r) of pid
    opened_file_list = get_the_opened_file_list(openfile_cursor, pid)
    # select the list of opened files (just written file)
    total_files = get_the_written_file_list(writefile_cursor)
    # select the parent id of pid from process list
    parent_id = get_the_parent_id(parent_cursor, pid)
    # Getting the total opened files from the spot-tools matrix file
    topenedf = []
    for file in opened_file_list:
        for line in total_files:
            if line[1] in file[1]:
                topenedf.append(file) if file not in topenedf else None
    # Create and add data process of pid to list
    process_node.add(topenedf, pid, parent_id, process_name, -1)
    # Calling the current function recursively for the children of the process
    for child in child_list:
        if child[0] is not None:
            process_node.append(pid, create_graph(child[0],
                                process_node, db_path))
    data = process_node.get_data(pid)
    return data


def get_the_child_processes(process_cursor, pid):
    """Return children of the process."""
    process_id_query = '''
            SELECT id
            FROM processes
            WHERE parent = %s
            '''
    process_cursor.execute(process_id_query % pid)
    return process_cursor.fetchall()


def get_the_processes_name(executed_cursor, pid):
    """Return the process name."""
    process_name_query = '''
                SELECT name, argv
                FROM executed_files
                WHERE process = %s
                '''
    executed_cursor.execute(process_name_query % pid)
    return executed_cursor.fetchall()


def get_the_opened_file_list(openfile_cursor, pid):
    """Return all opened files (W/R)."""
    opened_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE process = %s AND mode <= 2
            '''
    openfile_cursor.execute(opened_files_query % pid)
    return openfile_cursor.fetchall()


def get_the_written_file_list(writefile_cursor):
    """Return the written files (W)."""
    written_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE mode == 2
            '''
    writefile_cursor.execute(written_files_query)
    return writefile_cursor.fetchall()


def get_the_parent_id(parent_cursor, pid):
    """Return the parent id of the process."""
    process_parent_query = '''
                SELECT parent
                FROM processes
                WHERE id = %s
                '''
    parent_cursor.execute(process_parent_query % pid)
    return parent_cursor.fetchall()


def path_parser(path, subj_name):
    """Parse file path based on the subject folder name."""
    path = op.normpath(path)
    check = False
    for ind, file_name in enumerate(path.split('/')):
        if file_name == subj_name:
            check = True
            break
    if check is True:
        splited_path = "/".join(path.split('/')[ind+1:])
    else:
        splited_path = path
    return str(splited_path.strip('/'))


def flist_multi_write(pipeline_files, written_files_list,
                      pipeline_graph, subj_name):
    """Return list of total mutli-write process."""
    origin_p = {}
    for p_file in pipeline_files:
        p_file_name = str(p_file.split(" ")[0].strip('/'))
        # if int(n[1][:-1]) == 1:
        num_proc = []
        for f_totall in written_files_list:
            # if (int(n[1][:-1]) != 0 and str(n[0]) in data_parsed_name):
            if p_file_name == path_parser(str(f_totall[1]), str(subj_name)):
                # if p_file_name == 'T1w/103414/label/rh.cortex.label':
                #     print("here")
                file_name = os.path.abspath(str(f_totall[1]))
                if re.match("^.*.log$", file_name) is None and \
                   re.match("^.*.cmd$", file_name) is None and \
                   re.match("^.*.env$", file_name) is None:
                    proc_name = pipeline_graph.get_name(f_totall[0])
                    p_splited_name = str(proc_name[0][0]).split("/")[-1:]
                    if p_splited_name[0] not in ["recon-all", "awk"]:
                        num_proc.append(f_totall[0])
            num_proc = list(set(num_proc))
        if len(num_proc) > 1:
            origin_p[file_name] = num_proc
    log_info("Multi-write files are detected")
    return origin_p


def write_multi_write_files(output_file, origin, pipeline_graph):
    """Write output json file contains processes with multi-write files."""
    command_dic = {}
    command_lines = {}
    json_output = open(os.path.splitext(output_file)[0]+'_captured.json', 'w+')
    for p_name, pid_list in origin.items():
        for pid in pid_list:
            common_file = []
            proc_name = pipeline_graph.get_name(pid)
            if proc_name[0][1] in command_lines.keys():
                common_file = command_lines[proc_name[0][1]]['files']
            common_file.append(str(p_name))
            command_lines[(proc_name[0][1])] = {}
            command_lines[(proc_name[0][1])]['files'] = common_file
            command_lines[(proc_name[0][1])]['id'] = pid
    command_dic['total_multi_write_proc'] = command_lines
    json.dump(command_dic, json_output, indent=4, sort_keys=True)
    json_output.close()


def write_temp_files(output_file, temp_commands, info_):
    """Write output json file contains totall temporary files."""
    with open(os.path.splitext(output_file)[0]+'_captured.json', 'r') as rfile:
        data = json.load(rfile)
    data['execution_info'] = info_
    data['total_temp_proc'] = temp_commands
    with open(os.path.splitext(output_file)[0]+'_captured.json', 'w') as wfile:
        json.dump(data, wfile, indent=4, sort_keys=True)


def write_json_file(output_file, command_lines, multi_commands):
    """Wrtie output json file contains recognised processes."""
    data = {}
    with open(os.path.splitext(output_file)[0] +
              '_captured.json', 'w+') as wfile:
        json.dump(data, wfile, indent=4, sort_keys=True)
    try:
        with open(output_file, 'r') as rfile:
            data = json.load(rfile)
    except Exception:
        data = {}
    data['certain_cmd'] = command_lines
    data['multiWrite_cmd'] = multi_commands
    # data['execution_info'] = info_
    if multi_commands:
        try:
            for k in multi_commands.keys():
                if k not in data["total_commands_multi"].keys():
                    temp = {k: multi_commands[k]}
                    data["total_commands_multi"].update(temp)
                else:
                    temp_files = data["total_commands_multi"][k]["files"]
                    for f in multi_commands[k]["files"]:
                        if f not in data["total_commands_multi"][k]["files"]:
                            temp_files.append(f)
                    temp_id = data["total_commands_multi"][k]["id"]
                    if type(temp_id) is not list:
                        temp_id = [temp_id]
                    if multi_commands[k]["id"] not in temp_id:
                        temp_id.append(multi_commands[k]["id"])
                    new_process = {k: {"files": temp_files, "id": temp_id}}
                    data["total_commands_multi"].update(new_process)
            # data["total_commands_multi"].update(multi_commands)
        except Exception:
            data["total_commands_multi"] = multi_commands

    if command_lines:
        try:
            for k in command_lines.keys():
                if k not in data["total_commands"].keys():
                    temp = {k: command_lines[k]}
                    data["total_commands"].update(temp)
                else:
                    temp_files = data["total_commands"][k]["files"]
                    for f in command_lines[k]["files"]:
                        if f not in data["total_commands"][k]["files"]:
                            temp_files.append(f)
                    temp_id = data["total_commands"][k]["id"]
                    if type(temp_id) is not list:
                        temp_id = [temp_id]
                    if command_lines[k]["id"] not in temp_id:
                        temp_id.append(command_lines[k]["id"])
                    new_process = {k: {"files": temp_files, "id": temp_id}}
                    data["total_commands"].update(new_process)
            # d ata["total_commands"].update(command_lines)
        except Exception:
            data["total_commands"] = command_lines

    with open(output_file, 'w+') as json_file:
        json.dump(data, json_file, indent=4, sort_keys=True)


def diff_matrix_format(read_matrix_file):
    """Load difference matrix file."""
    log_info("read error matrix file between two conditions..")
    with open(read_matrix_file, 'r') as pfiles:
        data = json.load(pfiles)
    dic_data = data["condition1 vs condition2"]["files"]
    if dic_data == {}:
        quit()
    pipeline_files = []
    subj_name = (sorted(list(dic_data[
                  sorted(list(dic_data.keys()))[0]][
                  sorted(list(dic_data[
                   sorted(list(dic_data.keys()))[0]].keys()))[0]].keys()))
                 )[0]

    for file_name, file_dic in dic_data.items():
        pipeline_files.append(file_name + " " +
                              str(file_dic["subjects"][subj_name]["checksum"])
                              + os.linesep)
    # print(pipeline_files)
    # sys.exit("EXIT NOW !")
    # ~ for line in lines[1:]:
        # ~ splited_line = line.split('\t')
        # ~ pipeline_files.append(splited_line[0].replace(' ', '') + " " +
        #                      # ~ str(int(splited_line[1])) + os.linesep)
    return pipeline_files, subj_name


def add_tmp_path(data, file_name, subj_name):
    """Change the path of temporary files to the original path."""
    data = list(data)
    for ind, item in enumerate(op.normpath(data[1]).split('/')):
        if item == subj_name:
            break
    data[1] = op.join('/'.join(data[1].split('/')[:ind+1]), file_name)
    data = tuple(data)
    return data


def get_write_files(pipeline_files, proc, capture_mode, data_parsed_name,
                    write_diff_list, write_nodiff_list, write_tmp_list,
                    write_total_tmp, subj_name, data):
    """Label processes and corresponding files in W mode."""
    tmp_flag = True
    for diff_file in pipeline_files:
        temp_folder = 'spot_temp/'
        file_name = str(diff_file.split(" ")[0])
        file_stat = int(diff_file.split(" ")[1][:-1])

        if temp_folder in file_name and not capture_mode:
            data = add_tmp_path(data, file_name, subj_name)
            file_name = file_name.replace(temp_folder, '')

        if (file_stat != 0 and file_name == data_parsed_name):
            write_diff_list.append(data[0:2])
            tmp_flag = False
            break

        elif (file_stat == 0 and file_name == data_parsed_name):
            write_nodiff_list.append(data[0:2])
            tmp_flag = False
            break

    if tmp_flag:
        tmp_w = ()
        tmp_w = (proc.name[0][1], data[1])
        write_tmp_list.append(tmp_w)
        check_temp = False
        for t in write_total_tmp:
            if data[1] == t[1]:
                check_temp = True
        if check_temp is False:
            temp1 = (proc.name[0][1], data[1])
            write_total_tmp.append(temp1)
    return (write_diff_list, write_nodiff_list, write_tmp_list,
            write_total_tmp)


def get_read_files(pipeline_files, capture_mode, data_parsed_name, origin_p,
                   pipeline_graph, read_diff_list, read_nodiff_list,
                   read_tmp_list, subj_name, data):
    """Label processes and corresponding files in R mode."""
    tmp_flag = True
    for diff_file in pipeline_files:
        temp_folder = 'spot_temp/'
        file_name = str(diff_file.split(" ")[0])
        file_stat = int(diff_file.split(" ")[1][:-1])

        if temp_folder in file_name and not capture_mode:
            data = add_tmp_path(data, file_name, subj_name)
            file_name = file_name.replace(temp_folder, '')

        if (file_stat != 0 and file_name == data_parsed_name):
            data = data[:2] + (origin_p,)
            read_diff_list.append(data)
            tmp_flag = False
            break

        elif (file_stat == 0 and file_name == data_parsed_name):
            data = data[:2] + (origin_p,)
            read_nodiff_list.append(data)
            tmp_flag = False
            break

    if tmp_flag:
        if data[1] != '/dev/null':
            for orig in origin_p:
                p_name = pipeline_graph.get_name(orig)
                if p_name is not None:
                    tmp_r = (p_name[0][1], data[1], origin_p)
                    read_tmp_list.append(tmp_r)
    return (read_diff_list, read_nodiff_list, read_tmp_list)


def process_with_differences(write_diff_list, origin, proc, subj_name,
                             pipeline_graph, old_multi_commands,
                             multi_commands, ignored_multi, command_lines):
    """Add processes with differences include file with multi-write."""
    # for file in write_diff_list:
    #     key = str(file[1])
    #     if key in origin.keys():
    #         write_diff_list.remove(file)
    #         values = origin[key]
    #         if  proc.id in values:
    #             for v in sorted(values) ....
    for key, values in origin.items():
        if proc.id in values:
            # key is file name and value is pid of process,
            # So value should be counted by the proc timestamp
            for file in write_diff_list:
                f1 = path_parser(str(file[1]), subj_name)
                f2 = path_parser(key, subj_name)
                if f1 == f2:
                    write_diff_list.remove(file)
            for v in sorted(values):
                if v in ignored_multi:
                    continue
                var = True
                proc_name = pipeline_graph.get_name(v)
                common_file = [str(key)]
                if proc_name[0][1] in multi_commands.keys():
                    test = multi_commands[proc_name[0][1]]['files']
                    if common_file[0] not in \
                       multi_commands[proc_name[0][1]]['files']:
                        multi_commands[proc_name[0][1]]['files'].append(
                            common_file[0])
                    break
                if proc_name[0][1] in old_multi_commands.keys():
                    if common_file[0] not in \
                       old_multi_commands[proc_name[0][1]]['files']:
                        multi_commands[(proc_name[0][1])] = {}
                        multi_commands[(proc_name[0][1])]['files'] = (
                            old_multi_commands[proc_name[0][1]]['files'] +
                            [common_file[0]])
                        multi_commands[(proc_name[0][1])]['id'] = int(v)
                        break
                    var = False

                if var is True:
                    multi_commands[(proc_name[0][1])] = {}
                    multi_commands[(proc_name[0][1])]['files'] = (
                                                        common_file)
                    multi_commands[(proc_name[0][1])]['id'] = (
                                                        int(v))
                    break
    # add red process include file with no multi-write
    if write_diff_list:
        files = []
        for file in write_diff_list:
            files.append(str(file[1]))
        if "monitor.sh" not in proc.name[0][1]:
            command_lines[(proc.name[0][1])] = {}
            command_lines[(proc.name[0][1])]['files'] = files
            command_lines[(proc.name[0][1])]['id'] = int(proc.id)
    return multi_commands, command_lines


def parse_data(proc, pipeline_graph, pipeline_files, written_files_list,
               subj_name, capture_mode, list_of_files, ignore_list,
               write_total_tmp):
    # ###### FIND FILE DEPENDENCIES INCLUDE W/R PIPELINE AND
    # ###### TEMPORARY FILES WITH/WITHOUT DIFFERENCES
    write_diff_list = []
    write_nodiff_list = []
    write_tmp_list = []
    read_diff_list = []
    read_nodiff_list = []
    read_tmp_list = []
    for data in proc.data:
        # filter process by data
        if ignore_list:
            if filter_process_by_data(ignore_list, data,
                                      list_of_files,
                                      capture_mode):
                continue
        data_parsed_name = path_parser(str(data[1]), subj_name)
        if op.splitext(data_parsed_name)[1] == '':
            continue
        # check files in WRITE mode
        if data[2] == 2:
            (write_diff_list, write_nodiff_list, write_tmp_list,
             write_total_tmp) = get_write_files(pipeline_files, proc,
                                                capture_mode,
                                                data_parsed_name,
                                                write_diff_list,
                                                write_nodiff_list,
                                                write_tmp_list,
                                                write_total_tmp,
                                                subj_name, data)
        # check files in READ mode
        elif data[2] == 1:
            # continue if this file is written by the same process
            origin_p = get_origin_file(written_files_list, data)
            if proc.id in origin_p:
                continue
            # read_list.append(data[1])
            (read_diff_list, read_nodiff_list,
                read_tmp_list) = get_read_files(pipeline_files, capture_mode,
                                                data_parsed_name, origin_p,
                                                pipeline_graph,
                                                read_diff_list,
                                                read_nodiff_list,
                                                read_tmp_list,
                                                subj_name, data)
    return (read_diff_list, read_nodiff_list, read_tmp_list, write_diff_list,
            write_nodiff_list, write_tmp_list, write_total_tmp)


def filter_process_by_name(name):
    """Filter process by process name."""
    if name in ["cp", "tee", "date", "Null", "recon-all"]:
        return True
    return False


def filter_process_by_data(ignorefile, data, list_of_files, capture_mode):
    """Filter process by file name."""
    # data 'path' is from sqlite db
    # dname 'path' is from verify_files
    if not capture_mode:
        if op.basename(str(data[1])) not in list_of_files:
            return True
    ignore = []
    with open(ignorefile, 'r') as ignoref:
        ignore = ignoref.readlines()  # read the whole files
    for dname in ignore:
        if dname[:-2] in data[1]:
            return True
    return False


def get_origin_file(written_files_list, data):
    """Find the origin process of the files in R mode."""
    origin_p = []
    for o in written_files_list:
        if str(os.path.abspath(data[1])) == \
           str(os.path.abspath(str(o[1]))):
            origin_p.append(o[0])
    return origin_p


def check_file(parser, x):
    """Check if file exist."""
    if os.path.exists(x):
        return x
    parser.error("File does not exist: {}".format(x))


def read_old_multiwrite(output_file):
    """Read the last json file of multi-write process."""
    try:
        with open(output_file, 'r') as rfile:
            old_data = json.load(rfile)
            old_multi_commands = old_data["total_commands_multi"]
    except Exception:
        old_multi_commands = {}
    try:
        with open(output_file, 'r') as rfile:
            old_data = json.load(rfile)
            ignored_multi = old_data["ignored_multi"]
    except Exception:
        ignored_multi = []

    return old_multi_commands, ignored_multi


def log_info(message):
    logging.info("INFO: " + message)


def log_error(message):
    logging.error("ERROR: " + message)
    sys.exit(1)


def main(args=None):
    parser = argparse.ArgumentParser(description='Classification of the nodes'
                                                 ' in the pipeline graph.')
    parser.add_argument("sqlite_db",
                        type=lambda x: check_file(parser, x),
                        help='sqlite file created by reprozip, '
                             'includes all pipeline processes')
    parser.add_argument("matrix",
                        type=lambda x: check_file(parser, x),
                        help="matrix file produced by verify_files")
    parser.add_argument('-i', '--ignore',
                        type=lambda x: check_file(parser, x),
                        help='file containing process '
                             'names to ignore (one process name per line).')
    parser.add_argument('-o', '--output_file',
                        help='.Json output file include all commandlines of'
                              'uncertain, unknown, and certain red processes')
    parser.add_argument('-c', '--capture_mode', action='store_true',
                        help='include two values (true and false) to indicate'
                              'capture mode of the script'
                              'modification steps (false)'
                              'capturing temp and multi-write files'
                              'or making graph file (true)')
    parser.add_argument('-a', '--command_line',
                        help='pass the command line executed in the pipeline'
                              'to capture data that write differences')
    args = parser.parse_args(args)
    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
    # INITIALIZE THE PROGRAM
    if args.ignore:
        with open(args.ignore, 'r') as ignoref:
            exclude_items = [line.strip('\n') for line in ignoref]

    capture_mode = args.capture_mode
    if capture_mode:
        log_info("Capturing intermediate files...")
    else:
        log_info("Labeling processes...")

    db_path = args.sqlite_db
    read_matrix_file = args.matrix
    write_total_tmp = ['000']
    command_lines = {}
    multi_commands = {}
    temp_commands = {}
    info_ = {}
    old_multi_commands, ignored_multi = read_old_multiwrite(args.output_file)
    # read the pipeline files
    pipeline_files, subj_name = diff_matrix_format(read_matrix_file)
    list_of_files = [op.basename(str(f.split(' ')[0])) for f in pipeline_files]
    info_['subject_name'] = subj_name
    # CREATE PROCESS TREE
    # open the database file created by Reprozip tool
    log_info("Connecting to database..")
    db = sqlite3.connect(db_path)
    # db.text_factory = str
    writefile_cursor = db.cursor()
    # select the list of opened files (just written file)
    written_files_list = get_the_written_file_list(writefile_cursor)
    db.close()
    # start the program (pid of root process is 1)
    try:
        sys.setrecursionlimit(30000)
        with open(op.join(op.dirname(args.output_file),
                          "tmp_graph.pkl"), "rb") as tmp_fr:
            pipeline_graph = pickle.load(tmp_fr)
    except Exception:
        pipeline_graph = linked_list()
        create_graph(1, pipeline_graph, db_path)

        with open(op.join(op.dirname(args.output_file),
                          "tmp_graph.pkl"), "wb") as tmp_fw:
            pickle.dump(pipeline_graph, tmp_fw, pickle.HIGHEST_PROTOCOL)
    # time1 = time.time()
    # cmd = "/data/asalari/ali-tests/nurm-out/6/backup_scripts/
    # usr/local/src/tools/workbench/bin_rh_linux64/wb_command
    # -set-structure /data/asalari/ali-tests/PFS_Centos7_Traced/6/exec/exec/
    # 103414/T1w/103414/surf/lh.white.surf.gii CORTEX_LEFT"
    # dd = convert_to_key(cmd)
    # proc = pipeline_graph.get_data_name(convert_to_key(cmd))
    # proc2 = pipeline_graph.get_data_name(convert_to_key(args.command_line))

    # pipeline_graph.reverse()
    pipeline_graph.filter(exclude_items)
    # pipeline_graph.reverse()
    total_pipe_proc = pipeline_graph.to_list()
    log_info("Process tree created")
    # FINDING ALL THE PROCESSES WITH MULTI-WRITE IN PIPELINE
    origin = flist_multi_write(pipeline_files, written_files_list,
                               pipeline_graph, subj_name)
    log_info("Start to finding file dependencies in Read and Write mode\
             and then classifying process..")

    if args.command_line:
        cmd = args.command_line
        proc = pipeline_graph.get_data_name(convert_to_key(cmd))
        if proc is not None:
            (read_diff_list, read_nodiff_list, read_tmp_list,
             write_diff_list, write_nodiff_list, write_tmp_list,
             write_total_tmp) = (parse_data(proc, pipeline_graph,
                                            pipeline_files, written_files_list,
                                            subj_name, capture_mode,
                                            list_of_files, args.ignore,
                                            write_total_tmp))
    # CHECK IF PROCESSES CREATE DIFFERENCES THEN ADD TO COMMAND-LINE LIST
            if (len(read_diff_list) == 0 and len(write_diff_list) > 0):
                # print(proc.id)
                multi_commands, command_lines = (
                    process_with_differences(write_diff_list, origin, proc,
                                             subj_name, pipeline_graph,
                                             old_multi_commands,
                                             multi_commands,
                                             ignored_multi,
                                             command_lines))
    else:
        # PROCESS LABELING USING CREATED PROCESS TREE
        for proc in total_pipe_proc:
            # filter process by name
            name = "Null"
            if proc.name != []:
                name = str(proc.name[0][0].split('/')[-1])
            if filter_process_by_name(name):
                continue

    # FIND FILE DEPENDENCIES INCLUDE W/R PIPELINE AND
    # TEMPORARY FILES WITH/WITHOUT DIFFERENCES
            (read_diff_list, read_nodiff_list, read_tmp_list,
             write_diff_list, write_nodiff_list, write_tmp_list,
             write_total_tmp) = (parse_data(proc, pipeline_graph,
                                            pipeline_files, written_files_list,
                                            subj_name, capture_mode,
                                            list_of_files, args.ignore,
                                            write_total_tmp))

    # CHECK IF PROCESSES CREATE DIFFERENCES THEN ADD TO COMMAND-LINE LIST
            if (len(read_diff_list) == 0 and len(write_diff_list) > 0):
                # print(proc.id)
                multi_commands, command_lines = (
                    process_with_differences(write_diff_list, origin, proc,
                                             subj_name, pipeline_graph,
                                             old_multi_commands,
                                             multi_commands,
                                             ignored_multi,
                                             command_lines))

    # FIND TEMP PROCESSES THAT CREATE DIFFERENCES IN MODE W/R
            if capture_mode:
                if (len(read_diff_list) >= 0 or len(read_nodiff_list) >= 0 or
                    len(write_diff_list) >= 0 or
                    len(write_nodiff_list) >= 0) and \
                   len(write_tmp_list) > 0:
                    temp_w = []
                    for tmp in write_tmp_list:
                        if tmp[1] != '/dev/null':
                            temp_w.append(str(tmp[1]))
                    temp_commands[(proc.name[0][1])] = {}
                    temp_commands[(proc.name[0][1])]['files'] = temp_w
                    temp_commands[(proc.name[0][1])]['id'] = int(proc.id)

    # WRITE OUTPUT FILES
    # print(time.time()- time1)
    if capture_mode:
        # add total multi write processes for the first time
        write_multi_write_files(args.output_file, origin, pipeline_graph)
        write_temp_files(args.output_file, temp_commands, info_)
    else:
        write_json_file(args.output_file, command_lines, multi_commands)

    log_info("files captured and classified")


if __name__ == '__main__':
    main()
