#!/usr/bin/python

import os
import re
import argparse
import sqlite3
import json
import logging
import sys
import pandas as pd
from sqlite3 import Error
from graphviz import Digraph as Di


# the structure of each process in the pipeline
class node_structure:
    def __init__(self, initdata, pid, parent_id, process_name, level):
        self.id = pid
        self.name = process_name
        self.pid = parent_id
        self.data = initdata
        self.level = level
        self.next = None


# Include all the functions to create the list of processes
class linked_list:
    def __init__(self):
        self.head = None

    def is_empty(self):
        return (self.head is None)

    # Returns the size of the list
    def size(self):
        current = self.head
        count = 0
        while current is not None:
            count = count + 1
            current = current.next
        return count

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

    # Reverse the list which the head of list refer to the root process
    def reverse(self):
        prev = None
        current = self.head
        while (current is not None):
            next = current.next
            current.next = prev
            prev = current
            current = next
        self.head = prev
        return prev

    # keep the correspond processes in the pipeline
    # and remove the other processes
    def filter(self):
        prev = None
        current = self.head
        level_id = []
        level = 6
        while (current is not None):
            next = current.next
            if len(current.data) != 0:
                # keep just the files of its process
                data = current.data
                current.data = ()
                for d in data:
                    if d[0] == current.id:
                        current.data += (d,)
                # identifying the root process (as the main pipeline elements)
                if current.pid[0][0] is None:
                    level_id.append([current.id, 0])
                    current.level = 0
                    current.next = prev
                    prev = current
                # here we can expand the final result to
                # more sub-process details instead of first-level
                for line2 in level_id:
                    tmp = current.pid[0]
                    if line2[0] == tmp[0]:
                        if line2[1] < level:
                            level_id.append([current.id, line2[1] + 1])
                            current.level = line2[1] + 1
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

    # Remove the process from list
    def remove(self, item):
        current = self.head
        previous = None
        found = False
        while not found:
            if current.data == item:
                found = True
            else:
                previous = current
                current = current.next
        if previous is None:
            self.head = current.next
        else:
            previous.setNext(current.next)

    def get_name(self, item):
        current = self.head
        found = False
        while current is not None and not found:
            if current.id == item:
                return current.name
            else:
                current = current.next


# Idenfitying and classifying the whole processes of the pipeline
# based on the reprozip trace file
def create_graph(pid, process_node, db_path):
    try:
        db = sqlite3.connect(db_path)
    except Error as e:
        print (e)
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
    # Getting the total opened files from the repro-tools matrix file
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


# Update temp and multi write path name in sqlite db
def update_db_path():
    db = sqlite3.connect(db_path)
    process_cursor = db.cursor()
    path_update_query = '''
                        UPDATE opened_files SET name = %s
                        WHERE name = $s
                        and process = $s
                        '''
    process_cursor.execute(path_update_query % new_name % old_name % pid)
    return process_cursor.fetchall()


# Returns the children of the process
def get_the_child_processes(process_cursor, pid):
    process_id_query = '''
            SELECT id
            FROM processes
            WHERE parent = %s
            '''
    process_cursor.execute(process_id_query % pid)
    return process_cursor.fetchall()


# Returns the name of the process
def get_the_processes_name(executed_cursor, pid):
    process_name_query = '''
                SELECT name, argv
                FROM executed_files
                WHERE process = %s
                '''
    executed_cursor.execute(process_name_query % pid)
    return executed_cursor.fetchall()


# Returns the all opened files (W/R)
def get_the_opened_file_list(openfile_cursor, pid):
    opened_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE process = %s AND mode <= 2
            '''
    openfile_cursor.execute(opened_files_query % pid)
    return openfile_cursor.fetchall()


# Returns the written files (W)
def get_the_written_file_list(writefile_cursor):
    written_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE mode == 2
            '''
    writefile_cursor.execute(written_files_query)
    return writefile_cursor.fetchall()


# Returns the parent id of the process
def get_the_parent_id(parent_cursor, pid):
    process_parent_query = '''
                SELECT parent
                FROM processes
                WHERE id = %s
                '''
    parent_cursor.execute(process_parent_query % pid)
    return parent_cursor.fetchall()


# Node Creation functions
def make_yellow_node(graph, id, pid, name, node_label, read_diff_list,
                     read_tmp_list, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='yellow')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]),
               shape='circle')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    # showing the dependencies by dashed edges:
    # diff read(red), tmp read(yellow) and read files without error (green)
    for e2 in read_diff_list:
        graph.attr('edge', style='dashed', color='red')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_tmp_list:
        graph.attr('edge', style='dashed', color='yellow')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_nodiff_list:
        graph.attr('edge', style='dashed', color='green')
        for e in e2[2]:
            graph.edge(str(e), str(id))


def make_red_node(graph, id, pid, name, node_label, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='red')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]), shape='circle')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    for e2 in read_nodiff_list:
        graph.attr('edge', style='dashed', color='green')
        for e in e2[2]:
            graph.edge(str(e), str(id))


def make_squared_red_node(graph, id, pid, name, node_label,
                          read_tmp_list, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='red')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]), shape='square')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    for e2 in read_tmp_list:
        graph.attr('edge', style='dashed', color='yellow')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_nodiff_list:
        graph.attr('edge', style='dashed', color='green')
        for e in e2[2]:
            graph.edge(str(e), str(id))


def make_blue_node(graph, id, pid, name, node_label, read_diff_list,
                   read_tmp_list, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='blue')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]), shape='circle')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    for e2 in read_diff_list:
        graph.attr('edge', style='dashed', color='red')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_tmp_list:
        graph.attr('edge', style='dashed', color='yellow')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_nodiff_list:
        graph.attr('edge', style='dashed', color='green')
        for e in e2[2]:
            graph.edge(str(e), str(id))


def make_squared_blue_node(graph, id, pid, name, node_label, read_diff_list,
                           read_tmp_list, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='blue')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]), shape='square')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    for e2 in read_diff_list:
        graph.attr('edge', style='dashed', color='red')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_tmp_list:
        graph.attr('edge', style='dashed', color='yellow')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_nodiff_list:
        graph.attr('edge', style='dashed', color='green')
        for e in e2[2]:
            graph.edge(str(e), str(id))


def make_green_node(graph, id, pid, name, node_label, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='yellowgreen')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]), shape='circle')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    for e2 in read_nodiff_list:
        graph.attr('edge', style='dashed', color='green')
        for e in e2[2]:
            graph.edge(str(e), str(id))


def make_squared_green_node(graph, id, pid, name, node_label,
                            read_diff_list, read_tmp_list, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='yellowgreen')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]), shape='square')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    for e2 in read_diff_list:
        graph.attr('edge', style='dashed', color='red')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_tmp_list:
        graph.attr('edge', style='dashed', color='yellow')
        for e in e2[2]:
            graph.edge(str(e), str(id))
    for e2 in read_nodiff_list:
        graph.attr('edge', style='dashed', color='green')
        for e in e2[2]:
            graph.edge(str(e), str(id))


# ~ # Create a file include all dependency files info
def write_to_file(write_diff_list, read_diff_list, read_tmp_list,
                  write_tmp_list, write_files, proc, count_diff_w,
                  count_diff_r, count_tmp_r, count_tmp_w):
    wf = pd.DataFrame(write_diff_list, columns=['process_ID', 'name'])
    rf = pd.DataFrame(read_diff_list, columns=['process_ID', 'name',
                                               'created_process'])
    tr = pd.DataFrame(read_tmp_list, columns=['process_ID', 'name',
                                              'created_process'])
    tw = pd.DataFrame(write_tmp_list, columns=['process_ID', 'name'])
    write_files.write(str(proc.id) + "\t" + str(proc.name) +
                      "\ntotal write/read files:\t" + str(len(proc.data)) +
                      "\ntotal write files with diff: " +
                      str(count_diff_w) + "\n\n")
    wf.to_csv(write_files, sep='\t', index=False)
    write_files.write("\ntotal read files with diff: " +
                      str(count_diff_r) + "\n\n")
    rf.to_csv(write_files, sep='\t', index=False)
    write_files.write("\ntotal read temp files: " + str(count_tmp_r) + "\n\n")
    tr.to_csv(write_files, sep='\t', index=False)
    write_files.write("\ntotal write temp files: " + str(count_tmp_w) + "\n\n")
    tw.to_csv(write_files, sep='\t', index=False)
    write_files.write("\n************************************\n\n")


def path_parser(path):
    count = 0
    for f in path.split('/'):
        # if f == "exec":
        if f == "subject1":
            count += 1
            break
        else:
            count += 1
    splited_path = "/"+"/".join(path.split('/')[count:])
    return str(os.path.abspath(splited_path))


def flist_multi_write(pipeline_files, written_files_list, pipeline_graph):
    origin_p = {}
    for f in pipeline_files:
        n = f.split(" ")
        # if int(n[1][:-1]) != 0:
        if int(n[1][:-1]) == 1:
            num_proc = []
            for o in written_files_list:
                # if (int(n[1][:-1]) != 0 and str(n[0]) in data_parsed_name):
                if str("/" + n[0]) == path_parser(str(
                                      os.path.abspath(str(o[1])))):
                    file_name = str(os.path.abspath(str(o[1])))
                    if re.match("^.*.log$", file_name) is None and \
                       re.match("^.*.cmd$", file_name) is None and \
                       re.match("^.*.env$", file_name) is None:
                        proc_name = pipeline_graph.get_name(o[0])
                        p_splited_name = str(proc_name[0][0]).split("/")[-1:]
                        if p_splited_name[0] not in ["cp", "recon-all"]:
                            num_proc.append(o[0])
                num_proc = list(set(num_proc))
            if len(num_proc) > 1:
                origin_p[file_name] = num_proc
    log_info("Multi-write files are detected")
    return origin_p


def total_common_processes(output_file, origin, pipeline_graph):
    # Add the common processes based on the common files with differences
    # to prevent of propagating errors with various processes
    command_dic = {}
    command_lines = {}
    json_output = open(os.path.splitext(output_file)[0]+'_captured.json', 'w+')
    # ~ write_total_commons = open("total_common_cmd.txt", 'w')
    for key, values in origin.items():
        # if proc.id in values:
        for v in values:
            common_file = []
            proc_name = pipeline_graph.get_name(v)
            if proc_name[0][1] in command_lines.keys():
                common_file = command_lines[proc_name[0][1]]
            common_file.append(str(key))
            command_lines[(proc_name[0][1])] = common_file
    command_dic['total_multi_write_proc'] = command_lines
    json.dump(command_dic, json_output, indent=4, sort_keys=True)
    # ~ for key, val in command_lines.items():
    # ~ write_total_commons.write(str(key) + "##" + str(val) + "\n")
    json_output.close()


def write_temp_files(output_file, temp_commands):
    with open(os.path.splitext(output_file)[0]+'_captured.json', 'r') as rfile:
        data = json.load(rfile)
    data['total_temp_proc'] = temp_commands
    with open(os.path.splitext(output_file)[0]+'_captured.json', 'w') as wfile:
        json.dump(data, wfile, indent=4, sort_keys=True)


def error_matrix_format(read_matrix_file):
    log_info("read error matrix file between two conditions..")
    with open(read_matrix_file, 'r') as pfiles:
        data = json.load(pfiles)
    dat = data["centos6 vs centos7"]["files"]
    pipeline_files = []
    for file_name, file_dic in dat.items():
        # ~ print(file_dic["subjects"]["subject1"]["checksum"])
        pipeline_files.append(file_name + " " + str(file_dic["subjects"]["subject1"]["checksum"]) + os.linesep)
    #print(pipeline_files)
    #sys.exit("EXIT NOW !")
    # ~ for line in lines[1:]:
        # ~ splited_line = line.split('\t')
        # ~ pipeline_files.append(splited_line[0].replace(' ', '') + " " +
                              # ~ str(int(splited_line[1])) + os.linesep)
    return pipeline_files


def check_file(parser, x):
    if os.path.exists(x):
        return x
    parser.error("File does not exist: {}".format(x))


def log_info(message):
    logging.info("INFO: " + message)


def log_error(message):
    logging.error("ERROR: " + message)
    sys.exit(1)

def main():
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
    parser.add_argument('-g', '--graph',
                        help='dot file where the graph will be written. A'
                              'png rendering will also be done.')
    parser.add_argument('-o', '--output_file',
                        help='.Json output file include all commandlines of'
                              'uncertain, unknown, and certain red processes')
    parser.add_argument('-c', '--capture_mode',
                        help='include two values (true and false) to indicate'
                              'capture mode of the script'
                              'modification steps (false)'
                              'capturing temp and multi-write files'
                              'or making graph file (true)')
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
    # INITIALIZE THE PROGRAM
    if args.graph:
        graph = Di('Graph', filename=args.graph, format='png', strict=False)
    else:
        graph = Di('Graph', format='png', strict=False)

    # write_files = open("complete_file.txt", 'w')
    # write_proc = open("all_processes", 'w')
    write_total_tmp = ['000']
    write_total_tmp2 = ['000']
    node_label = 0
    proc_list = []
    total_processes = {}
    command_lines = {}
    multi_commands = {}
    temp_commands = {}
    red_nodes = []
    blue_nodes = []
    ignore = []
    capture_mode = args.capture_mode
    if capture_mode == 'true':
        capture_mode = True
        log_info("Prepare to capturing files")
    else:
        capture_mode = False
        log_info("Prepare to classifying process")
    db_path = args.sqlite_db
    read_matrix_file = args.matrix
    # read the pipeline files
    pipeline_files = error_matrix_format(read_matrix_file)
    if args.ignore:
        with open(args.ignore, 'r') as ignorefiles:
            ignore = ignorefiles.readlines()  # read the whole files
    # CREATE PROCESS TREE
    # Open the database file contains all the processes
    log_info("Connecting to database..")
    db = sqlite3.connect(db_path)
    writefile_cursor = db.cursor()
    # Select the list of opened files (just written file)
    written_files_list = get_the_written_file_list(writefile_cursor)
    db.close()
    # Start the program (pid of root process is 1)
    pipeline_graph = linked_list()
    create_graph(1, pipeline_graph, db_path)
    pipeline_graph.reverse()
    pipeline_graph.filter()
    pipeline_graph.reverse()
    total_pipe_proc = pipeline_graph.to_list()
    log_info("Process tree created")

    # FINDING ALL THE PROCESSES WITH MULTI-WRITE IN PIPELINE
    origin = flist_multi_write(pipeline_files, written_files_list,
                               pipeline_graph)
    log_info("Start to finding file dependencies in Read and Write mode\
             and then classifying process..")
    # PROCESS CLASSIFICATION USING CREATED PROCESS TREE
    for proc in total_pipe_proc:
        count_diff_w = 0
        count_nodiff_w = 0
        count_tmp_w = 0
        count_diff_r = 0
        count_tmp_r = 0
        count_nodiff_r = 0
        write_diff_list = []
        write_nodiff_list = []
        write_tmp_list = []
        read_diff_list = []
        read_nodiff_list = []
        read_tmp_list = []

# ##########
# ###### FIND FILE DEPENDENCIES INCLUDE W/R PIPELINE AND
# ###### TEMPORARY FILES WITH/WITHOUT ERRORS
# ####
        for data in proc.data:
            tn = True
            for nn in ignore:
                if nn[:-2] in data[1]:
                    tn = False
                    break
            if tn is False:
                continue
            data_parsed_name = path_parser(str(data[1]))
            # check if file with WRITE mode
            if data[2] == 2:
                check_list = False
                for t in write_total_tmp2:
                    if data[1] == t[1]:
                        check_list = True
                if check_list is False:
                    write_total_tmp2.append(data[0:2])
                tmp = False
                for diff in pipeline_files:
                    n = diff.split(" ")
                    check_temp_file = False
                    file_name = str("/" + n[0])
                    if 'peds_temp/' in n[0] and not capture_mode:
                        check_temp_file = True
                        temp_folder = '/peds_temp/'
                        temp_file_name = n[0].replace(
                                         'peds_temp/', '').split('_')
                        file_name = "/" + '_'.join(temp_file_name[1:])
                    if int(n[1][:-1]) != 0 and \
                       file_name == data_parsed_name:
                        if check_temp_file:
                            data = list(data)
                            nn = data[1].split('/')
                            new_n = temp_folder + nn[-1]
                            data[1] = '/'.join(nn[:-1]) + new_n
                            data = tuple(data)

                        write_diff_list.append(data[0:2])
                        count_diff_w += 1
                        tmp = True
                        break
                    elif (int(n[1][:-1]) == 0 and
                          file_name == data_parsed_name):
                        if check_temp_file:
                            data = list(data)
                            nn = data[1].split('/')
                            new_n = temp_folder + nn[-1]
                            data[1] = '/'.join(nn[:-1]) + new_n
                            data = tuple(data)

                        write_nodiff_list.append(data[0:2])
                        count_nodiff_w += 1
                        tmp = True
                        break
                if tmp is False:
                    tmp_w = ()
                    tmp_w = (proc.name[0][1], data[1])
                    write_tmp_list.append(tmp_w)
                    count_tmp_w += 1
                    check_temp = False
                    for t in write_total_tmp:
                        if data[1] == t[1]:
                            check_temp = True
                    if check_temp is False:
                        temp1 = (proc.name[0][1], data[1])
                        write_total_tmp.append(temp1)

            # check if file with READ mode
            elif data[2] == 1:
                # finding the origin process of the files in R mode
                # to show dependencies
                origin_p = []
                for o in written_files_list:
                    if str(os.path.abspath(data[1])) == \
                       str(os.path.abspath(str(o[1]))):
                        origin_p.append(o[0])
                if proc.id in origin_p:
                    continue
                # read_list.append(data[1])
                tmp = False
                for diff2 in pipeline_files:
                    n = diff2.split(" ")
                    check_temp_file = False
                    file_name = str("/" + n[0])
                    if 'peds_temp/' in n[0] and not capture_mode:
                        check_temp_file = True
                        temp_folder = '/peds_temp/'
                        temp_file_name = n[0].replace(
                                         'peds_temp/', '').split('_')
                        file_name = "/" + '_'.join(temp_file_name[1:])
                    if (int(n[1][:-1]) != 0 and
                            file_name == data_parsed_name):
                        if check_temp_file:
                            data = list(data)
                            nn = data[1].split('/')
                            new_n = temp_folder + nn[-1]
                            data[1] = '/'.join(nn[:-1]) + new_n
                            data = tuple(data)

                        data = data[:2] + (origin_p,)
                        read_diff_list.append(data)
                        count_diff_r += 1
                        tmp = True
                        break
                    elif (int(n[1][:-1]) == 0 and
                          file_name == data_parsed_name):
                        if check_temp_file:
                            data = list(data)
                            nn = data[1].split('/')
                            new_n = temp_folder + nn[-1]
                            data[1] = '/'.join(nn[:-1]) + new_n
                            data = tuple(data)

                        data = data[:2] + (origin_p,)
                        read_nodiff_list.append(data)
                        count_nodiff_r += 1
                        tmp = True
                        break
                if tmp is False:
                    if data[1] != '/dev/null':
                        for orig in origin_p:
                            p_name = pipeline_graph.get_name(orig)
                            if p_name is not None:
                                tmp_r = (p_name[0][1], data[1], origin_p)
                                read_tmp_list.append(tmp_r)
                    count_tmp_r += 1

# ##########
# ###### IGNORE PROCESSES BY NAME
# ####
        name = "Null"
        if proc.name != []:
            name = str(proc.name[0][0].split('/')[-1])
        if name == "tee" or name == "date" or name == "Null":
            continue

# ##########
# ###### FIND RED PROCESSES (CREATE ERROR) AND CREATE COMMAND-LINES LIST
# ####
        # check if RED process
        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r >= 0:
            # add red process include file with multi-write
            is_multi = False
            for key, values in origin.items():
                if proc.id in values:
                    is_multi = True
                    # key is file name and value is pid of process,
                    # So value should be counted by the proc timestamp
                    for v in values:
                        common_file = []
                        proc_name = pipeline_graph.get_name(v)
                        common_file.append(str(key))
                        command_str = (str((proc_name[0][1])) +
                                       "##" + str(common_file) + '\n')
                        try:
                            with open(args.output_file, 'r') as rfile:
                                data = json.load(rfile)
                                multi_commands = data["multiWrite_cmd"]
                        except:
                            multi_commands = {}
                        var = True
                        for key2, val in multi_commands.items():
                            cmd = str(key2) + "##" + str(val) + '\n'
                            if cmd == command_str:
                                var = False
                        if var is True:
                            multi_commands[(proc_name[0][1])] = common_file
                            # ~ command_lines[(proc_name[0][1])] = common_file
                            break
                        # # ~ common_processes.append(str(v) + " = "
                        #                          # ~ + str(proc_name[0][0]))
            # add red process include file with no multi-write
            if (not is_multi):
                files = []
                temp_file = []
                path = name
                if proc.name != []:
                    path = str(proc.name[0][0])
                    pid = str(proc.id)
                for file in write_diff_list:
                    files.append(str(file[1]))
                for tmp in write_tmp_list:
                    temp_file.append(str(tmp[1]))
                if "monitor.sh" not in proc.name[0][1]:
                    red_nodes.append(pid + " = " + path)
                    command_lines[(proc.name[0][1])] = files

        # check if BLUE process
        elif (count_diff_r > 0 and (count_nodiff_w > 0 or count_tmp_w > 0)
              and count_diff_w == 0 and count_tmp_w == 0):
            if name != "md5sum":
                path = name
                if proc.name != []:
                    path = str(proc.name[0][0])
                    pid = str(proc.id)
                    blue_nodes.append(pid + " = " + path)

# ##########
# ###### FIND TEMP PROCESSES THAT CREATE ERROR IN MODE W/R
# ####
        if capture_mode:
            if (count_diff_r > 0 or count_nodiff_r > 0 or count_diff_w > 0 or
               count_nodiff_w > 0) and count_tmp_w > 0:
                temp_w = []
                for tmp in write_tmp_list:
                    if tmp[1] != '/dev/null':
                        temp_w.append(str(tmp[1]))
                temp_commands[(proc.name[0][1])] = temp_w

            # # ~ if ((count_diff_r > 0 or count_nodiff_r > 0 or
            #     # ~ count_diff_w > 0 or count_nodiff_w > 0) and
            #    # ~ count_tmp_r > 0):
            #     # ~ for tmp2 in read_tmp_list:
            #         # ~ check = []
            #         # ~ p_splited_name = str(tmp2[0]).split("/")[-1:]
            #         # ~ if p_splited_name[0] not in ["cp", "recon-all"]:
            #             # ~ if tmp2[0] in temp_commands.keys():
            #                 # ~ check = temp_commands[tmp2[0]]
            #             # ~ check.append(tmp2[1])
            #             # ~ temp_commands[tmp2[0]] = check

# ##########
# ###### MAKE PROCESS GRAPH VISUALIZATION (DOT FILE)
# ####
        # According to the read/write files, classify process by colored node:
        # create(red), propagate(yellow), remove(blue) and
        # green nodes are process with no differences
        if count_diff_r > 0 and count_diff_w > 0:
            make_yellow_node(graph, proc.id, proc.pid, name, node_label,
                             read_diff_list, read_tmp_list, read_nodiff_list)
            proc_list.append([node_label, proc.id, len(proc.data),
                              count_diff_r, count_nodiff_r, count_tmp_r,
                              count_diff_w, count_nodiff_w, count_tmp_w,
                              proc.name])
            node_label += 1

        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r == 0:
            make_red_node(graph, proc.id, proc.pid, name, node_label,
                          read_nodiff_list)
            proc_list.append([node_label, proc.id, len(proc.data),
                             count_diff_r, count_nodiff_r, count_tmp_r,
                             count_diff_w, count_nodiff_w, count_tmp_w,
                             proc.name])
            node_label += 1

        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r > 0:
            make_squared_red_node(graph, proc.id, proc.pid, name,
                                  node_label, read_tmp_list, read_nodiff_list)
            proc_list.append([node_label, proc.id, len(proc.data),
                             count_diff_r, count_nodiff_r, count_tmp_r,
                             count_diff_w, count_nodiff_w, count_tmp_w,
                             proc.name])
            node_label += 1

        elif (count_diff_r > 0 and (count_nodiff_w > 0 or count_tmp_w > 0) and
              count_diff_w == 0 and count_tmp_w == 0):
            if name != "md5sum":
                make_blue_node(graph, proc.id, proc.pid, name, node_label,
                               read_diff_list, read_tmp_list, read_nodiff_list)
                proc_list.append([node_label, proc.id, len(proc.data),
                                 count_diff_r, count_nodiff_r, count_tmp_r,
                                 count_diff_w, count_nodiff_w, count_tmp_w,
                                 proc.name])
                node_label += 1

        elif count_diff_r > 0 and count_diff_w == 0 and count_tmp_w > 0:
            make_squared_blue_node(graph, proc.id, proc.pid, name,
                                   node_label, read_diff_list,
                                   read_tmp_list, read_nodiff_list)
            proc_list.append([node_label, proc.id, len(proc.data),
                              count_diff_r, count_nodiff_r, count_tmp_r,
                              count_diff_w, count_nodiff_w, count_tmp_w,
                              proc.name])
            node_label += 1

        elif (count_diff_r == 0 and count_tmp_r == 0 and count_diff_w == 0
              and count_tmp_w == 0):
            make_green_node(graph, proc.id, proc.pid, name, node_label,
                            read_nodiff_list)
            proc_list.append([node_label, proc.id, len(proc.data),
                              count_diff_r, count_nodiff_r, count_tmp_r,
                              count_diff_w, count_nodiff_w, count_tmp_w,
                              proc.name])
            node_label += 1

        # # ~ elif (count_diff_r==0 and count_tmp_r>0 and
        #       # ~ count_diff_w==0 and count_tmp_w>0):
        else:
            make_squared_green_node(graph, proc.id, proc.pid, name,
                                    node_label, read_diff_list,
                                    read_tmp_list, read_nodiff_list)
            proc_list.append([node_label, proc.id, len(proc.data),
                              count_diff_r, count_nodiff_r, count_tmp_r,
                              count_diff_w, count_nodiff_w, count_tmp_w,
                              proc.name])
            node_label += 1

    if args.graph:
        graph.render()
        log_info(".png graph file created")

# ##########
# ###### WRITE OUTPUT FILES
# ####

    if capture_mode:
        # add total multi write processes for the first time
        total_common_processes(args.output_file, origin, pipeline_graph)
        write_temp_files(args.output_file, temp_commands)
    else:
        data = {}
        with open(os.path.splitext(args.output_file)[0] +
                  '_captured.json', 'w+') as wfile:
            json.dump(data, wfile, indent=4, sort_keys=True)

    try:
        with open(args.output_file, 'r') as rfile:
            data = json.load(rfile)
    except:
        data = {}
    data['certain_cmd'] = command_lines
    data['multiWrite_cmd'] = multi_commands
    with open(args.output_file, 'w+') as json_file:
        json.dump(data, json_file, indent=4, sort_keys=True)
    log_info("files captured and classified")


if __name__ == '__main__':
    main()
