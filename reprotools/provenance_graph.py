import zss
import argparse
import os
import re
import sqlite3
import hashlib
import json
from sqlite3 import Error
from graphviz import Digraph as Di


# Returns the children of the process
def get_the_child_processes(process_cursor, pid):
    process_id_query = '''
            SELECT id
            FROM processes
            WHERE parent = %s
            '''
    process_cursor.execute(process_id_query % pid)
    child_list = process_cursor.fetchall()
    chlst = []
    for child2 in child_list:
        chlst.append(child2[0])
    return chlst


# Returns the process name
def get_the_processes_name(executed_cursor, pid):
    process_name_query = '''
                SELECT name, argv
                FROM executed_files
                WHERE process = %s
                '''
    executed_cursor.execute(process_name_query % pid)
    process_name = executed_cursor.fetchall()
    if process_name != []:
        process_name = str(process_name[0][0]).split('/')[-1:][0]
    else:
        process_name = ""
    return process_name


# Returns all opened files (both W/R modes)
def get_opened_files_list(openfile_cursor, pid):
    opened_files_query = '''
            SELECT process, name, mode, id
            FROM opened_files
            WHERE process = %s AND mode <= 2
            '''
    openfile_cursor.execute(opened_files_query % pid)
    return openfile_cursor.fetchall()


def create_provenance_graph(db_path, pid, graph_, pipe_list=[], multi_list={},
                            tmp_list=[], total_proc_diff=[]):
    try:
        db = sqlite3.connect(db_path)
    except Error as e:
        print(e)
    process_cursor = db.cursor()
    executed_cursor = db.cursor()
    openfile_cursor = db.cursor()
    # Get the list of child process from pid
    child_list = get_the_child_processes(process_cursor, pid)
    # Get the process name
    process_name = get_the_processes_name(executed_cursor, pid)
    # Get the list of opened files (w/r) from pid
    process_ofiles = get_opened_files_list(openfile_cursor, pid)

    # graph_.attr('node', shape='circle', style='filled', fillcolor='white')
    if pid in total_proc_diff:
        graph_.node(str(pid), ''.join([str(pid), '#', process_name]),
                    shape='circle', style='filled', fillcolor='red')
    else:
        graph_.node(str(pid), ''.join([str(pid), '#', process_name]),
                    shape='circle', style='filled', fillcolor='green')

    for file in process_ofiles:
        fname_ = str(os.path.basename(file[1]))
        file_code = str(file[1])
        if fname_ in multi_list.keys():
            if file[2] == 2:
                file_code = str(file[1]) + str(pid)
            else:
                sorted_ = sorted(multi_list[fname_])
                for pid_lst in sorted_:
                    if pid > pid_lst:
                        set_pid = pid_lst
                        continue
                file_code = str(file[1]) + str(set_pid)

        hash_object = hashlib.sha1(file_code.encode('utf-8'))
        hex_dig_file = hash_object.hexdigest()
        # Read files
        if file[2] == 1 and str(hex_dig_file) in pipe_list:
            graph_.attr('edge', style='dashed')
            graph_.edge(str(hex_dig_file), str(pid))

        # Write files
        elif file[2] == 2 and (fname_ in pipe_list or fname_ in tmp_list):
            if str(hex_dig_file) not in pipe_list:
                pipe_list.append(str(hex_dig_file))
            graph_.attr('node', shape='box', style='filled', fillcolor='white')
            if fname_ in tmp_list or fname_ in multi_list.keys():
                graph_.attr('node', style='filled', fillcolor='grey')
            graph_.node(str(hex_dig_file), ''.join([str(pid), '#', fname_]))
            graph_.attr('edge', style='dashed')
            graph_.edge(str(pid), str(hex_dig_file))

    for child in child_list:
        p_name_child = get_the_processes_name(executed_cursor, child)
        if p_name_child not in ["", "date", "imtest", "mkdir", "imcp",
                                "basename", "remove_ext", "rm", "awk",
                                "grep", "cp", "cat", "fslval", "fslhead",
                                "fslhd", "expr", "head", "fslreorient2std"]:
            graph_.attr('edge', style='solid')
            graph_.edge(str(pid), str(child))
            create_provenance_graph(db_path, child, graph_, pipe_list,
                                    multi_list, tmp_list, total_proc_diff)


def parse_transient(tr_file):
    try:
        with open(tr_file, 'r') as cfile:
            data = json.load(cfile)
            if "total_temp_proc" not in data:
                tmp_write = []
            else:
                tmp_write = []
                tmp_write_dic = data["total_temp_proc"]
                for key, file_ in tmp_write_dic.items():
                    for tmp in file_['files']:
                        ntmp = tmp.encode('utf8', 'ignore') \
                                  .replace('\x00', ' ').strip()
                        tmp_write.append(os.path.basename(ntmp))

            if "total_multi_write_proc" not in data:
                multi_write = {}
            else:
                multi_write = {}
                multi_write_t = data["total_multi_write_proc"]
                for key, file_ in multi_write_t.items():
                    for mw in file_['files']:
                        fname = os.path.basename(mw.encode('utf8',
                                                           'ignore').strip())
                        if fname not in multi_write.keys():
                            multi_write[fname] = [file_['id']]
                        else:
                            tmp_list = multi_write[fname]
                            tmp_list.append(file_['id'])
                            multi_write[fname] = tmp_list
    except Exception:
        multi_write = {}
        tmp_write = []
    return multi_write, tmp_write


def parse_labelling(diff_processes):
    try:
        with open(diff_processes, 'r') as cfile:
            data = json.load(cfile)
            if "total_commands" not in data:
                list_p = []
            else:
                list_p = []
                tmp_write_dic = data["total_commands"]
                for key, file_ in tmp_write_dic.items():
                    list_p.append(file_['id'])

            if "total_commands_multi" in data:
                multi_write_t = data["total_commands_multi"]
                for key, file_ in multi_write_t.items():
                    list_p.append(file_['id'])

    except Exception:
        list_p = []
    return list_p


def main(args=None):
    parser = argparse.ArgumentParser(description='Provenance graph '
                                                 'representations')
    parser.add_argument("input_folder",
                        help='input folder of pipeline results ')
    parser.add_argument("output_folder",
                        help='output folder to save the figures each '
                             'provenance graph using graphviz')
    parser.add_argument('-r', '--reprozipfile',
                        help='trace file from reprozip ')
    parser.add_argument('-t', '--transient',
                        help='list of transient files ')
    parser.add_argument('-l', '--labelling',
                        help='List of processes that create differences')

    args = parser.parse_args(args)
    input_folder = args.input_folder
    output_folder = args.output_folder
    db_file = args.reprozipfile
    diff_processes = args.labelling
    tr_file = args.transient
    multi_list, tmp_list = parse_transient(tr_file)
    total_proc_diff = parse_labelling(diff_processes)

    # Get the list of output files
    lst_files = []
    for file in os.walk(input_folder):
        for elem in file[2]:
            lst_files.append(elem)
    # Create provenance graphs
    graph = Di('Graph',
               filename=os.path.join(output_folder, "provenance_graph"),
               format='svg',
               strict=True)
    # graph.attr(compound=True)
    create_provenance_graph(db_file, 1, graph, lst_files, multi_list,
                            tmp_list, total_proc_diff)
    graph.render()


if __name__ == '__main__':
    main()
