#!/usr/bin/python

import os, re
import argparse
import sqlite3
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

#Include all the functions to create the list of processes
class linked_list:
    def __init__(self):
        self.head = None
    def is_empty(self):
        return self.head == None
    #Returns the size of the list
    def size(self):
        current = self.head
        count = 0
        while current != None:
            count = count + 1
            current = current.next
        return count
    #Returns the list of graph nodes
    def to_list(self):
        current = self.head
        result = []
        while current != None:
            result.append(current)
            current = current.next
        return result
    #Add the new node(process) to list
    def add(self, item, pid, parent_id, process_name, level):
        new_node = node_structure(item, pid, parent_id, process_name, level)
        new_node.next = self.head
        self.head = new_node
    #Reverse the list which the head of list refer to the root process
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
    #keep the involved processes in the pipeline and remove the other processes
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
                if current.pid[0][0] == None:
                    level_id.append([current.id, 0])
                    current.level = 0
                    current.next = prev
                    prev = current
                # here we can expand the final result to more sub-process details instead of first-level
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
    #Add new data to the process data when the program is aggregated
    def append(self, pid,newfiles):
        current = self.head
        found = False
        while current != None and not found:
            if current.id == pid:
                current.data += newfiles
                found = True
            else:
                current = current.next
    #Returns the data of process
    def get_data(self, item):
        current = self.head
        found = False
        while current != None and not found:
            if current.id == item:
                return current.data
            else:
                current = current.next
    #Remove the process from list
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
        if previous == None:
            self.head = current.next
        else:
            previous.setNext(current.next)

    def get_name(self, item):
        current = self.head
        found = False
        while current != None and not found:
            if current.id == item:
                return current.name
            else:
                current = current.next

#Idenfitying and classifying the whole processes of the pipeline based on the reprozip trace file
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

    #select the list of child process of pid
    child_list = get_the_child_processes(process_cursor, pid)
    #select the process name
    process_name = get_the_processes_name(executed_cursor, pid)
    #select the list of opened files (w/r) of pid
    opened_file_list = get_the_opened_file_list(openfile_cursor, pid)
    #select the list of opened files (just written file)
    total_files = get_the_written_file_list(writefile_cursor)
    #select the parent id of pid from process list
    parent_id = get_the_parent_id(parent_cursor, pid)
    topenedf = []  # Getting the total opened files from the repro-tools matrix file
    for file in opened_file_list:
        for line in total_files:
            if line[1] in file[1]:
                topenedf.append(file) if file not in topenedf else None
    #Create and add data process of pid to list
    process_node.add(topenedf, pid, parent_id, process_name, -1)
    #Calling the current function recursively for the children of the process
    for child in child_list:
        if child[0] != None:
            process_node.append(pid, create_graph(child[0], process_node, db_path))
    data = process_node.get_data(pid)
    return data

#Returns the children of the process
def get_the_child_processes(process_cursor, pid):
    process_id_query = '''
            SELECT id
            FROM processes
            WHERE parent = %s
            '''
    process_cursor.execute(process_id_query % pid)
    return process_cursor.fetchall()

#Returns the name of the process
def get_the_processes_name(executed_cursor, pid):
    process_name_query = '''
                SELECT name, argv
                FROM executed_files
                WHERE process = %s
                '''
    executed_cursor.execute(process_name_query % pid)
    return executed_cursor.fetchall()

#Returns the all opened files (W/R)
def get_the_opened_file_list(openfile_cursor, pid):
    opened_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE process = %s AND mode <= 2 
            '''
    openfile_cursor.execute(opened_files_query % pid)
    return openfile_cursor.fetchall()

#Returns the written files (W)
def get_the_written_file_list(writefile_cursor):
    written_files_query = '''
            SELECT process, name, mode
            FROM opened_files
            WHERE mode == 2 
            '''
    writefile_cursor.execute(written_files_query)
    return writefile_cursor.fetchall()

#Returns the parent id of the process
def get_the_parent_id(parent_cursor, pid):
    process_parent_query = '''
                SELECT parent
                FROM processes
                WHERE id = %s
                '''
    parent_cursor.execute(process_parent_query % pid)
    return parent_cursor.fetchall()

#Node Creation functions
def make_yellow_node(graph, id, pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list):
    graph.attr('node', style='filled', fillcolor='yellow')
    graph.node(str(id), ''.join(
        [str(node_label), '#', name]),
               shape='circle')
    graph.attr('edge', style='solid', color='black')
    graph.edge(str(pid[0][0]), str(id))
    # showing the dependencies by dashed edges: diff read(red), tmp read(yellow)
    # and read files without differences(green)
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

def make_squared_red_node(graph, id, pid, name, node_label, read_tmp_list, read_nodiff_list):
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

def make_blue_node(graph, id, pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list):
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

def make_squared_blue_node(graph, id, pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list):
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

def make_squared_green_node(graph, id, pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list):
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

#Create a file include all dependency files info
def write_to_file(write_diff_list, read_diff_list, read_tmp_list, write_tmp_list, write_files, proc, count_diff_w, count_diff_r, count_tmp_r, count_tmp_w):
    wf = pd.DataFrame(write_diff_list, columns=['process_ID', 'name'])
    rf = pd.DataFrame(read_diff_list, columns=['process_ID', 'name', 'created_process'])
    tr = pd.DataFrame(read_tmp_list, columns=['process_ID', 'name', 'created_process'])
    tw = pd.DataFrame(write_tmp_list, columns=['process_ID', 'name'])
    write_files.write(str(proc.id) + "\t" + str(proc.name) + "\ntotal write/read files:\t" + str(len(proc.data)) +
                      "\ntotal write files with diff: " + str(count_diff_w) + "\n\n")
    wf.to_csv(write_files, sep='\t', index=False)
    write_files.write("\ntotal read files with diff: " + str(count_diff_r) + "\n\n")
    rf.to_csv(write_files, sep='\t', index=False)
    write_files.write("\ntotal read temp files: " + str(count_tmp_r) + "\n\n")
    tr.to_csv(write_files, sep='\t', index=False)
    write_files.write("\ntotal write temp files: " + str(count_tmp_w) + "\n\n")
    tw.to_csv(write_files, sep='\t', index=False)
    write_files.write("\n************************************\n\n")

def path_parser(path):
    count = 0
    for f in path.split('/'):
        #if f == "exec":
        if f == "centos7":
            count += 1
            break
        else:
            count += 1
    splited_path = "/"+"/".join(path.split('/')[count:])
    return str(os.path.abspath(splited_path))

def print_writtn_files_by_several_process(pipeline_files, written_files_list, pipeline_graph):
    origin_p = {}
    for f in pipeline_files:
        n = f.split(" ")
        # if int(n[1][:-1]) != 0:
        if int(n[1][:-1]) == 1:
            num_proc = []
            for o in written_files_list:
                #     if (int(n[1][:-1]) != 0 and str(n[0]) in data_parsed_name):
                if str("/" + n[0]) == path_parser(str(os.path.abspath(str(o[1])))):
                    file_name = str(os.path.abspath(str(o[1])))
                    if re.match("^.*.log$", file_name) == None and re.match("^.*.cmd$",file_name) == None and re.match("^.*.env$", file_name) == None:
                        proc_name = pipeline_graph.get_name(o[0])
                        p_splited_name = str(proc_name[0][0]).split("/")[-1:]
                        if p_splited_name[0] not in ["cp", "recon-all"]:
                            num_proc.append(o[0])
                num_proc = list(set(num_proc))
            if len(num_proc) > 1:
                origin_p[file_name] = num_proc
    return origin_p

def main():
    parser = argparse.ArgumentParser(description='Classification of the pipeline processes and making its graph')
    parser.add_argument("-db", "--sqliteDB",
                        help="The path to the sqlite file which is created by reprozip trace and includes all pipeline process")
    parser.add_argument("-ofile", "--openedFiles",
                        help="refers to the matrix file of output of the 'repro-tools' script")
    args = parser.parse_args()

## INITIALIZE THE PROGRAM
    graph = Di('Graph', filename='GraphModel', format='dot', strict=False)
    #write_files = open("complete_file.txt", 'w')
    #write_proc = open("all_processes", 'w')
    write_total_tmp = ['000']
    write_total_tmp2 = ['000']
    node_label = 0
    proc_list = []
    command_lines = {}
    multi_commands = {}
    temp_commands = {}
    red_nodes = []
    blue_nodes = []
    common_processes = []
    
    db_path = args.sqliteDB
    read_matrix_file = args.openedFiles
    # read the pipeline files
    with open(read_matrix_file, 'r') as pfiles:
        pipeline_files = pfiles.readlines()
    try:
        with open("toremove.txt", 'r') as ignorefiles:
            ignore = ignorefiles.readlines()  # read the whole files
    except: ignore = []
  
## CREATE PROCESS TREE
    #Open the database file contains all the processes
    db = sqlite3.connect(db_path)
    writefile_cursor = db.cursor()
    #Select the list of opened files (just written file)
    written_files_list = get_the_written_file_list(writefile_cursor)
    db.close()
    #Start the program (pid of root process is 1)
    pipeline_graph = linked_list()
    create_graph(1, pipeline_graph, db_path)
    pipeline_graph.reverse()
    pipeline_graph.filter()
    pipeline_graph.reverse()
    total_pipe_proc = pipeline_graph.to_list()

## FINDING ALL THE PROCESSES WITH MULTI-WRITE IN PIPELINE
    origin = print_writtn_files_by_several_process(pipeline_files, written_files_list, pipeline_graph)
 #   '''
 #   # Add the common processes based on the common files with differences to prevent of propagating errors with various processes
 #   write_total_commons = open("total_common_cmd.txt", 'w')
 #   for key, values in origin.items():
 #       # if proc.id in values:
 #       for v in values:
 #           common_file = []
 #           proc_name = pipeline_graph.get_name(v)
 #           if proc_name[0][1] in command_lines.keys(): common_file = command_lines[proc_name[0][1]]
 #           common_file.append(str(key))
 #           command_lines[(proc_name[0][1])] = common_file
 #   for key, val in command_lines.items():
 #       write_total_commons.write(str(key) + "##" + str(val) + "\n")
 #   '''
## PROCESS CLASSIFICATION USING CREATED PROCESS TREE
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

###########
####### FIND FILE DEPENDENCIES INCLUDE W/R PIPELINE AND TEMPORARY FILES WITH/WITHOUT ERRORS
#####
        for data in proc.data:
            tn = True
            for nn in ignore:
                if nn[:-2] in data[1]:
                    tn = False
                    break
            if tn == False: continue
            data_parsed_name = path_parser(str(data[1]))
            # check if file with WRITE mode
            if data[2] == 2: 
                check_list = False
                for t in write_total_tmp2:
                    if data[1] == t[1]: check_list = True
                if check_list == False: write_total_tmp2.append(data[0:2])
                tmp = False
                for diff in pipeline_files:
                    n = diff.split(" ")
                    if (int(n[1][:-1]) != 0 and str("/" + n[0]) == data_parsed_name):
                        write_diff_list.append(data[0:2])
                        count_diff_w += 1
                        tmp = True
                        break
                    elif (int(n[1][:-1]) == 0 and str("/" + n[0]) == data_parsed_name):
                        write_nodiff_list.append(data[0:2])
                        count_nodiff_w += 1
                        tmp = True
                        break
                if tmp == False:
                    tmp_w = ()
                    tmp_w = (proc.name[0][1], data[1])
                    write_tmp_list.append(tmp_w)
                    count_tmp_w += 1
                    check_temp = False
                    for t in write_total_tmp:
                        if data[1] == t[1]: check_temp = True
                    if check_temp == False:
                        temp1 = (proc.name[0][1], data[1])
                        write_total_tmp.append(temp1)
                        
            # check if file with READ mode
            elif data[2] == 1:
                # finding the origin process of the read files to show dependencies
                origin_p = []
                for o in written_files_list:
                    if str(os.path.abspath(data[1])) == str(os.path.abspath(str(o[1]))):
                        origin_p.append(o[0])
                if proc.id in origin_p: continue
                # read_list.append(data[1])
                tmp = False
                for diff2 in pipeline_files:
                    n = diff2.split(" ")
                    if (int(n[1][:-1]) != 0 and str("/"+n[0]) == data_parsed_name):
                        data = data[:2] + (origin_p,)
                        read_diff_list.append(data)
                        count_diff_r += 1
                        tmp = True
                        break
                    elif (int(n[1][:-1]) == 0 and str("/"+n[0]) == data_parsed_name ):
                        data = data[:2] + (origin_p,)
                        read_nodiff_list.append(data)
                        count_nodiff_r += 1
                        tmp = True
                        break
                if tmp == False:
                    if data[1]!='/dev/null':
                        for orig in origin_p:
                            p_name = pipeline_graph.get_name(orig)
                            if p_name != None:
                                tmp_r = (p_name[0][1], data[1], origin_p)
                                read_tmp_list.append(tmp_r)
                    count_tmp_r += 1
                    
###########
####### IGNORE PROCESSES BY NAME
#####
        name = "Null"
        if proc.name != []: name = str(proc.name[0][0].split('/')[-1])
        if name == "tee" or name == "date" or name == "Null": continue
            
###########
####### FIND RED PROCESSES (CREATE ERROR) AND CREATE COMMAND-LINES LIST 
#####
        # check if RED process
        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r >= 0:
            # add red process include file with multi-write 
            is_multi = False
            for key, values in origin.items():
                if proc.id in values:
                    is_multi = True
                    for v in values:
                        common_file = []
                        proc_name = pipeline_graph.get_name(v)
                        common_file.append(str(key))
                        command_str = str((proc_name[0][1])) + "##" + str(common_file) + '\n'
                        try:
                            with open("common_cmd.txt", 'r') as c_proc:
                                common_proc = c_proc.readlines()
                        except: common_proc = []
                        tmp =True
                        for cmd in common_proc:
                            if cmd == command_str: tmp =False
                        if tmp == True:
                            multi_commands[(proc_name[0][1])] = common_file
                            command_lines[(proc_name[0][1])] = common_file
                            break
                        common_processes.append(str(v) + " = " + str(proc_name[0][0]))
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
        elif count_diff_r > 0 and (count_nodiff_w>0 or count_tmp_w>0) and count_diff_w == 0 and count_tmp_w == 0:
          if name != "md5sum":
            path = name
            if proc.name != []:
                path = str(proc.name[0][0])
                pid = str(proc.id)
                blue_nodes.append(pid + " = " + path)

###########
####### FIND PROCESSES THAT W/R TEMPORARY FILES AND CREATE TEMP COMMAND-LINES LIST 
#####
        if (count_diff_r > 0 or count_nodiff_r > 0 or count_diff_w > 0 or count_nodiff_w > 0) and count_tmp_w > 0:
            temp_w = []
            for tmp in write_tmp_list:
                if tmp[1] != '/dev/null': temp_w.append(str(tmp[1]))
            temp_commands[(proc.name[0][1])] = temp_w

        if (count_diff_r > 0 or count_nodiff_r > 0 or count_diff_w > 0 or count_nodiff_w > 0) and count_tmp_r > 0:
            for tmp2 in read_tmp_list:
                check = []
                p_splited_name = str(tmp2[0]).split("/")[-1:]
                if p_splited_name[0] not in ["cp", "recon-all"]:
                    if tmp2[0] in temp_commands.keys(): check = temp_commands[tmp2[0]]
                    check.append(tmp2[1])
                    temp_commands[tmp2[0]] = check

###########
####### MAKE PROCESS GRAPH VISUALIZATION (DOT FILE)
#####
        #According to the read/write files, classify the various process by colored node: create(red),
        #propagate(yellow), remove(blue) and green nodes are process with no differences
        if count_diff_r > 0 and count_diff_w > 0:
            make_yellow_node(graph, proc.id, proc.pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list)
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1

        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r == 0:
            make_red_node(graph, proc.id, proc.pid, name, node_label, read_nodiff_list)
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1

        elif count_diff_r == 0 and count_diff_w > 0 and count_tmp_r > 0:
            make_squared_red_node(graph, proc.id, proc.pid, name, node_label, read_tmp_list, read_nodiff_list)
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1

        elif count_diff_r > 0 and (count_nodiff_w>0 or count_tmp_w>0) and count_diff_w == 0 and count_tmp_w == 0:
          if name !="md5sum":
            make_blue_node(graph, proc.id, proc.pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list)
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1

        elif count_diff_r > 0 and count_diff_w == 0 and count_tmp_w > 0:
            make_squared_blue_node(graph, proc.id, proc.pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list)
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1

        elif count_diff_r == 0 and count_tmp_r == 0 and count_diff_w == 0 and count_tmp_w == 0:
            make_green_node(graph, proc.id, proc.pid, name, node_label, read_nodiff_list)
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1

        # elif count_diff_r==0 and count_tmp_r>0 and count_diff_w==0 and count_tmp_w>0:
        else:
            make_squared_green_node(graph, proc.id, proc.pid, name, node_label, read_diff_list, read_tmp_list, read_nodiff_list)
            proc_list.append(
                [node_label, proc.id, len(proc.data), count_diff_r, count_nodiff_r, count_tmp_r, count_diff_w,
                 count_nodiff_w, count_tmp_w, proc.name])
            node_label += 1
        #write_to_file(write_diff_list, read_diff_list, read_tmp_list, write_tmp_list, write_files, proc, count_diff_w,
        #              count_diff_r, count_tmp_r, count_tmp_w)

    #wproc = pd.DataFrame(proc_list, columns = ['node', 'process_ID', 'total_R/W', 'read_diff', 'read_no_diff',
    #                                         'read_temp', 'write_diff', 'write_no_diff',
    #                                         'wite_temp', 'process_name'])
    #wproc.to_csv(write_proc, sep ='\t', index = False)
    #graph.render()
    #graph.view()
    
###########
####### WRITE OUTPUT FILES
#####
    write_commands = open("command_lines.txt", 'w')
    write_total_commands = open("total_commands.txt", 'a+')
    write_commons = open("common_cmd.txt", 'a+')
    #write_temp_commands = open("total_tmp_files.txt", 'w')
    #write_interesting_nodes = open("interesting_nodes.txt", 'a+')
    # write temporary file
    #for key , val in temp_commands.items():
    #    write_temp_commands.write(str(key) +"##"+ str(val)+"\n")
    
    for key, val in command_lines.items():
        key = key.replace('\x00' or ' ',' ')
        #print(str(key) +"##"+ str(val))
        write_commands.write(str(key) +"##"+ str(val)+"\n")
        write_total_commands.write(str(key) +"##"+ str(val)+"\n")
    with open("common_cmd.txt", 'r') as c_proc:
        write_commands.write(c_proc.read())
        write_total_commands.write(c_proc.read())

    for key, val in multi_commands.items():
        write_commons.write(str(key) +"##"+ str(val)+"\n")
    #for key, val in interesting_nodes.items():
    #write_interesting_nodes.write("red nodes: "+str(red_nodes) +"\n"+"blue nodes: "+ str(blue_nodes)+"\n"+"common processes: "+ str(common_processes)+ "\n")
    #write_interesting_nodes.write("#### NEXT ITERATION ####\n\n")

if __name__=='__main__':
    main();
