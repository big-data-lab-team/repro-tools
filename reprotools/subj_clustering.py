#!/usr/bin/python

"""Subject Clustering and Result Analysis.

Using this script, we are able to clusster subjects in the dataset
based on the process tree and also plot the results of SPOT-tool.
"""

import zss
import argparse
import os
import re
import sqlite3
from sqlite3 import Error
from scipy.cluster.hierarchy import fcluster, dendrogram, linkage, fclusterdata
from sklearn.preprocessing import LabelEncoder
import numpy as np
import matplotlib
matplotlib.use('Agg')  # noqa
import matplotlib.pyplot as plt


def check_file(parser, x):
    if os.path.exists(x):
        return x
    parser.error("File does not exist: {}".format(x))


def strdist(a, b):
    if a == b:
        return 0
    else:
        return 0.1


class WeirdNode(object):

    def __init__(self, label):
        self.my_label = label
        self.my_children = list()

    @staticmethod
    def get_children(node):
        return node.my_children

    @staticmethod
    def get_label(node):
        return node.my_label

    def addkid(self, node, before=False):
        if before:
            self.my_children.insert(0, node)
        else:
            self.my_children.append(node)
        return self


def clustering_process_trees(db_file_list, threshold, output_folder):
    indofsubj = le.transform(db_file_list)
    pairs_fin = ([[x] for i, x in enumerate(indofsubj)])
    ss = np.array(pairs_fin)
    linked = linkage(np.array(pairs_fin), metric=edit_dist)
    fclust1 = fcluster(linked, t=threshold, criterion='distance')

    indices = cluster_indices(fclust1)
    output = os.path.join(output_folder, "clusters.txt")
    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))
    clusterfiles = open(output, 'w+')
    label_list = []
    for k, ind in enumerate(indices):
        basename_list = []
        for x in ind:
            x = db_file_list[x]
            basename_list.append(os.path.splitext(os.path.basename(x))[0])
            label_list.append(os.path.splitext(os.path.basename(x))[0])
        out_str = "cluster" + str(k + 1) + " is " + str(basename_list) + "\n"
        print(out_str)
        clusterfiles.writelines(out_str)
    # label_list = range(1, 101)
    plt.figure(figsize=(10, 7))
    dendrogram(linked,
               orientation='top',
               labels=label_list,
               distance_sort='descending',
               show_leaf_counts=True)
    plt.savefig(output_folder+'hclusters.png')
    # plt.show()


def edit_dist(p1, p2):
    # global pipe_proc
    lst = []
    lst.append(int(p1[0]))
    lst.append(int(p2[0]))
    out_list = le.inverse_transform(lst)
    f1 = out_list[0]
    f2 = out_list[1]
    root = (WeirdNode("root"))
    p_tree = make_process_tree(f1, root, pipe_proc, 1)
    root2 = (WeirdNode("root"))
    p_tree2 = make_process_tree(f2, root2, pipe_proc, 1)
    dist = zss.simple_distance(p_tree, p_tree2, WeirdNode.get_children,
                               WeirdNode.get_label, strdist)
    print("Distance %s vs %s is %s" % (f1, f2, dist))
    # if dist == 0:
    #     return 5
    return dist


def cluster_indices(cluster_assignments):
    n = cluster_assignments.max()
    indices = []
    for cluster_number in range(1, n + 1):
        indices.append(np.where(cluster_assignments == cluster_number)[0])
    return indices


def make_process_tree(db_path, root, pipe_proc, pid):
    try:
        db = sqlite3.connect(db_path)
    except Error as e:
        print(e)
    process_cursor = db.cursor()
    executed_cursor = db.cursor()

    # select the list of child process of pid
    child_list = get_the_child_processes(process_cursor, pid)
    for child in child_list:
        p_name_child = get_the_processes_name(executed_cursor, child)
        p_args_child = get_the_processes_args(executed_cursor, child)
        if (p_name_child in pipe_proc) or \
           (os.path.splitext(p_name_child)[1] == '.sh'):

            # if p_name_child not in ["", "date", "mkdir", "imcp", "basename",
            #                         "remove_ext", "rm", "awk", "grep", "cp",
            #                         "cat", "fslval", "fslhead", "fslhd",
            #                         "pwd", "expr", "tee", "head", "find",
            #                         "sort", "xargs", "rpm", "uname",
            #                         "touch", "which", "wc", "egrep"]:
            root.addkid(make_process_tree(
                            db_path, WeirdNode(p_args_child),
                            pipe_proc, child))
    return root


# returns the children of the process
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


# returns the name of the process
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


# returns the name of the process
def get_the_processes_args(executed_cursor, pid):
    process_name_query = '''
                SELECT name, argv
                FROM executed_files
                WHERE process = %s
                '''
    executed_cursor.execute(process_name_query % pid)
    process_args = executed_cursor.fetchall()
    if process_args != []:
        process_args = convert_to_key(process_args[0][1])
    else:
        process_args = ""
    return process_args


def convert_to_key(k):
    lst = []
    ss = k.split('\x00')
    for l in ss:
        lst.append(l.split('/')[-1])
    return ' '.join(lst)


def get_db_list(input_folder):
    db_list_files = []
    for filename in os.listdir(input_folder):
        if os.path.splitext(os.path.basename(filename))[1] == '.sqlite3':
            db_list_files.append(os.path.join(input_folder, filename))
            test = get_processes_list(os.path.join(input_folder, filename))
            lst = []
            for i in test:
                lst.append(str(os.path.basename(i[0])))
    return db_list_files, lst


def get_processes_list(db_path):
    try:
        db = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        print(e)
    execp_cursor = db.cursor()
    # add <or name == '/bin/cp'>
    process_name_query = '''
            SELECT distinct name
            FROM executed_files
            WHERE (name like '%/usr/local/src/fsl/%'
            or name like '%/usr/local/src/freesurfer/%'
            or name like '%/usr/local/src/tools/%')
            and name <> '/usr/local/src/fsl/bin/imtest'
            and name <> '/usr/local/src/fsl/bin/imcp'
            '''
    execp_cursor.execute(process_name_query)
    return execp_cursor.fetchall()


def main(args=None):
    parser = argparse.ArgumentParser(description='Classification of the nodes'
                                                 ' in the pipeline graph.')
    parser.add_argument("input_folder",
                        help='input folder of sqlite databases ')
    parser.add_argument("output_folder",
                        help='output folder to save clusters, plots, '
                             'and figures.')
    parser.add_argument('-t', '--threshold',
                        help='The threshold is defined as the minimum '
                             'distance required to separate clusters')

    args = parser.parse_args(args)
    input_folder = args.input_folder
    output_folder = args.output_folder

    # get a list of input db files and all pipeline processes
    db_file_list, pipe_process = get_db_list(input_folder)
    global pipe_proc
    pipe_proc = pipe_process
    # start of hierarchical clustering of process trees
    global le
    le = LabelEncoder()
    le.fit(db_file_list)
    clustering_process_trees(db_file_list, args.threshold, output_folder)


if __name__ == '__main__':
    main()
