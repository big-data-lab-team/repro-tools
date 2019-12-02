#!/usr/bin/python

"""Subject Clustering and Result Analysis.

Using this script, we are able to clusster subjects in the dataset
based on the process tree and also plot the results of NURM-tool.
"""

import zss
import argparse
import os
import re
import sqlite3
from sqlite3 import Error
from graphviz import Digraph as Di
import scipy
from scipy.cluster.hierarchy import fcluster, dendrogram, linkage, fclusterdata
from sklearn.preprocessing import LabelEncoder
import numpy as np
import matplotlib
matplotlib.use('Agg')  # noqa
import matplotlib.pyplot as plt
import matplotlib as mpl
import json
import sys
import seaborn as sns
from pylab import *
import plotly.graph_objects as go
from collections import Counter


def strdist(a, b):
    if a == b:
        return 0
    else:
        return 0.1

# def strdist(s1, s2):
#     m=len(s1)+1
#     n=len(s2)+1

#     tbl = {}
#     for i in range(m): tbl[i,0]=i
#     for j in range(n): tbl[0,j]=j
#     for i in range(1, m):
#         for j in range(1, n):
#             cost = 0 if s1[i-1] == s2[j-1] else 1
#             tbl[i,j] = min(tbl[i, j-1]+1, tbl[i-1, j]+1, tbl[i-1, j-1]+cost)

#     return tbl[i,j]


def check_file(parser, x):
    if os.path.exists(x):
        return x
    parser.error("File does not exist: {}".format(x))


def weird_dist(A, B):
    return 10*strdist(A, B)


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
    linked = linkage(np.array(pairs_fin), metric=edit_dist)
    fclust1 = fcluster(linked, t=threshold, criterion='distance')

    indices = cluster_indices(fclust1)
    clusterfiles = open(output_folder+"clusters.txt", 'w+')
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
    global pipe_proc
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
                               WeirdNode.get_label, weird_dist)
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


def get_subj_process_args(db_path, pid, subsets_dic, interest_list):
    try:
        db = sqlite3.connect(db_path)
    except Error as e:
        print(e)
    process_cursor = db.cursor()
    executed_cursor = db.cursor()

    # select the list of child process of pid
    process_name = get_the_processes_name(executed_cursor, pid)
    child_list = get_the_child_processes(process_cursor, pid)
    p_args_child = get_the_processes_args(executed_cursor, pid)

    subsets_dic = pipeline_element_frequesncy(process_name, subsets_dic,
                                              child_list, pid,
                                              p_args_child, interest_list)
    for child in child_list:
        process_name = get_the_processes_name(executed_cursor, child)
        if process_name not in ["", "date", "mkdir", "imcp", "basename",
                                "remove_ext", "rm", "awk", "grep", "cp", "cat",
                                "fslval", "fslhead", "fslhd", "expr", "head"]:

            get_subj_process_args(db_path, child, subsets_dic, interest_list)
            # root.addkid(get_subj_process_args(db_path,
            #             WeirdNode(p_args_child), child))
    return subsets_dic


def pipeline_element_frequesncy(process_name, subsets_dic, child_list, pid,
                                p_args_child, interest_list):
    if process_name in ['ACPCAlignment.sh', 'BrainExtraction_FNIRTbased.sh',
                        'T2wToT1wDistortionCorrectAndReg.sh',
                        'BiasFieldCorrection_sqrtT1wXT1w.sh',
                        'AtlasRegistrationToMNI152_FLIRTandFNIRT.sh',
                        'AnatomicalAverage.sh']:
        process_name = process_name.split('.')[0].split('_')[0]
        if process_name in subsets_dic.keys():
            new = subsets_dic[process_name]['subsets'] + child_list
            subsets_dic[process_name]['subsets'] = new
        else:
            sets = [pid] + child_list
            subsets_dic[process_name] = {}
            subsets_dic[process_name]['subsets'] = sets
            subsets_dic[process_name]['p_list'] = {}

    else:
        for p in subsets_dic.keys():
            if pid in subsets_dic[p]['subsets']:
                new = subsets_dic[p]['subsets'] + child_list
                subsets_dic[p]['subsets'] = new
                if process_name in interest_list:
                    if process_name not in ['wb_command', 'new_invwarp']:
                        process_name = process_name.split('.')[0].split('_')[0]

                    if process_name in ['fslmaths', 'fugue']:
                        p_args_child = (
                            re.sub(
                                r"fsl_......_tmp", "fsl_X_tmp", p_args_child)
                             )
                        p_args_child = (
                            re.sub(
                                r"......_3T_FieldMap_Magnitude",
                                "X_3T_FieldMap_Magnitude", p_args_child)
                            )
                        if ('fslmaths FieldMap -sub ' in p_args_child) or \
                           ('fslmaths T1wmulT2w_brain_norm_modulate -thr '
                           in p_args_child) or \
                           ('fslmaths T1wmulT2w_brain.nii.gz -div '
                           in p_args_child):
                            p_args_child = (
                                re.sub(r"(\b|\s+\-?|^\-?)(\d+|\d*\.\d+)\b",
                                       " X", p_args_child)
                                )

                    if process_name in subsets_dic[p]['p_list'].keys():
                        if (p_args_child in
                           subsets_dic[p]['p_list'][process_name].keys()):
                            new = (subsets_dic[p]['p_list']
                                   [process_name][p_args_child] + 1)
                            (subsets_dic[p]['p_list'][process_name]
                             [p_args_child]) = new
                        else:
                            (subsets_dic[p]['p_list'][process_name]
                             [p_args_child]) = 1
                    else:
                        subsets_dic[p]['p_list'][process_name] = {}
                        (subsets_dic[p]['p_list'][process_name]
                         [p_args_child]) = 1

    return subsets_dic


def ratio_of_diff_process(input_folder, interest_list, sep_item_freq):
    freq_dic = {}
    total_freq = {}
    i = 0
    for filename in os.listdir(input_folder):
        if os.path.splitext(os.path.basename(filename))[1] == '.sqlite3':
            subsets_dic = {}
            i = i + 1
            freq_dic[i] = get_subj_process_args(os.path.join(input_folder,
                                                             filename),
                                                1, subsets_dic, interest_list)

            for key in freq_dic[i].keys():
                if key not in total_freq.keys():
                    total_freq[key] = {}
                for p_name in freq_dic[i][key]['p_list'].keys():
                    if p_name not in total_freq[key].keys():
                        total_freq[key][p_name] = {}
                    for p_arg in freq_dic[i][key]['p_list'][p_name].keys():
                        if p_arg not in total_freq[key][p_name].keys():
                            total_freq[key][p_name][p_arg] = 1
                        else:
                            total_freq[key][p_name][p_arg] = (
                                total_freq[key][p_name][p_arg] + 1)

    for element in total_freq.keys():
        for proc_name in total_freq[element].keys():
            for proc_arg in total_freq[element][proc_name].keys():
                if proc_arg in sep_item_freq[proc_name].keys():
                    total_freq[element][proc_name][proc_arg] = (
                        str(sep_item_freq[proc_name][proc_arg]) + " outof " +
                        str(total_freq[element][proc_name][proc_arg]))
                    sep_item_freq[proc_name][proc_arg] = 0
                else:
                    total_freq[element][proc_name][proc_arg] = (
                        "0" + " outof " + str(
                            total_freq[element][proc_name][proc_arg]))

    # Add other red processes that are created outside the pipeline elements
    for pname in sep_item_freq.keys():
        for parg in sep_item_freq[pname].keys():
            if sep_item_freq[pname][parg] != 0:
                if 'others' not in total_freq.keys():
                    total_freq['others'] = {}
                if pname not in total_freq['others'].keys():
                    total_freq['others'][pname] = {}
                total_freq['others'][pname][parg] = sep_item_freq[pname][parg]

    return freq_dic, total_freq


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


def get_total_item_frequency(process_freq):
    total_process_freq = {}
    for key in process_freq.keys():
        for proc in process_freq[key].keys():
            if key not in total_process_freq.keys():
                total_process_freq[key] = process_freq[key][proc]
            else:
                total_process_freq[key] = (
                    total_process_freq[key] + process_freq[key][proc])
    return total_process_freq


def get_item_frequency(input_folder):
    process_freq = {}
    db_list_files = []
    for filename in os.listdir(input_folder):
        if os.path.splitext(os.path.basename(filename))[1] == '.sqlite3':
            db_list_files.append(os.path.join(input_folder, filename))
            test = get_processes_list(os.path.join(input_folder, filename))
            lst = []
            for i in test:
                lst.append(str(os.path.basename(i[0])))
        elif os.path.splitext(os.path.basename(filename))[1] == '.json':
            p_red_dic = {}
            p_key = []
            with open(os.path.join(input_folder, filename), 'r') as dprocess:
                data = json.load(dprocess)
            p_red_dic.update(data["total_commands"])
            if "total_commands_multi" in data.keys():
                p_red_dic.update(data["total_commands_multi"])
            # p_red_dic.update(data["removes_cmd"])
            for p in p_red_dic.keys():
                proc = str(convert_to_key(p).split(' ')[0])
                if proc != 'cp':
                    p_key.append(convert_to_key(p))
            for key in p_key:
                key = re.sub(r"fsl_......_tmp", "fsl_X_tmp", key)
                key = re.sub(r"......_3T_FieldMap_Magnitude",
                             "X_3T_FieldMap_Magnitude", key)
                if 'fslmaths FieldMap -sub ' in key or \
                   'fslmaths T1wmulT2w_brain_norm_modulate -thr ' in key or \
                   'fslmaths T1wmulT2w_brain.nii.gz -div ' in key:
                    key = re.sub(r"(\b|\s+\-?|^\-?)(\d+|\d*\.\d+)\b",
                                 " X", key)
                process_name = str(key.split(' ')[0])
                if process_name not in process_freq.keys():
                    process_freq[process_name] = {}
                    process_freq[process_name][key] = 1
                elif key not in process_freq[process_name].keys():
                    process_freq[process_name][key] = 1
                else:
                    process_freq[process_name][key] = (
                        process_freq[process_name][key] + 1)

    total_freq = get_total_item_frequency(process_freq)
    return total_freq, process_freq, db_list_files, lst


def plot_heatmap(subsets_dic, interesting_p, output_folder):
    ylabels = list(subsets_dic.keys())
    for ind, item in enumerate(ylabels):
        if item == 'T2wToT1wDistortionCorrectAndReg':
            ylabels[ind] = "DistortionCorrection"
        elif item == 'AtlasRegistrationToMNI152':
            ylabels[ind] = "AtlasRegistration"

    short_name = {}
    for lab in ylabels:
        if lab == 'ACPCAlignment':
            short_name['ACPCAlignment'] = 'AAli'
        elif lab == 'BrainExtraction':
            short_name['BrainExtraction'] = 'BExt'
        elif lab == 'AnatomicalAverage':
            short_name['AnatomicalAverage'] = 'AAve'
        elif lab == 'BiasFieldCorrection':
            short_name['BiasFieldCorrection'] = 'BFC'
        elif lab == 'DistortionCorrection':
            short_name['T2wToT1wDistortionCorrectAndReg'] = 'DC'
        elif lab == 'AtlasRegistration':
            short_name['AtlasRegistrationToMNI152'] = 'AR'

    startcolor = '#008000'
    midcolor = '#FFD700'
    endcolor = '#C00A0A'
    own_cmap1 = mpl.colors.LinearSegmentedColormap.from_list(
                    'own2', [startcolor, midcolor, endcolor])
    j = -1
    first = 0
    # grid = plt.GridSpec(len(ylabels)+1, len(interesting_p)+1,
    #                     hspace=0.05, wspace=0.05)
    fig, axes = plt.subplots(len(ylabels), len(interesting_p),
                             figsize=(47, 18))
    plt.subplots_adjust(hspace=0.05, wspace=0.04)
    cbar_ax = fig.add_axes([.91, .2, .02, .6])
    cbar_ax.tick_params(labelsize=26)
    for element in subsets_dic.keys():
        xlabels = {}
        j = j + 1

        for proc in subsets_dic[element].keys():
            if proc not in xlabels.keys():
                xlabels[proc] = []
            for parg in subsets_dic[element][proc].keys():
                if parg not in xlabels[proc]:
                    xlabels[proc].append(parg)
        i = 0
        for xlab in xlabels.keys():
            xlabel_ = []
            i = interesting_p.index(xlab)
            for y in xlabels[xlab]:
                xlabel_.append(y)

            frequency_matrix = []
            heatmap_label = []
            x = element
            freq_list = []
            freq_label = []
            for index, lab in enumerate(xlabel_):
                ch = True
                for y in subsets_dic[x].keys():
                    if lab in subsets_dic[x][y]:
                        ch = False
                        a, b = subsets_dic[x][y][lab].split(' outof ')
                        freq_list.append(float(a)/float(b))
                        freq_label.append(
                            str(float(a)/float(b))+' ['+str(b)+']')
                if ch is True:
                    freq_list.append(0)
                    freq_label.append('0 ['+str(b)+']')
            frequency_matrix.append(freq_list)
            heatmap_label.append(freq_label)
            xlabel_ = [str(x).split(' ')[0] for x in xlabel_]
            sns.set(font_scale=1.1)
            my_annot_kws = {"size": 30}  # , "weight":"bold"
            counted_ = list(Counter(frequency_matrix[0]).values())
            frequency_matrix = [list(Counter(frequency_matrix[0]).keys())]
            heatmap_label = [Counter(heatmap_label[0]).keys()]
            heatmap_label2 = [[]]
            for ind, val in enumerate(frequency_matrix[0]):
                for val_c in heatmap_label[0]:
                    hh = val_c.split(' ')[0]
                    if val_c.split(' ')[0] == str(val):
                        if counted_[ind] > 1:
                            val_c = val_c + ' x ' + str(counted_[ind])
                            heatmap_label2[0].append(val_c)
                        else:
                            heatmap_label2[0].append(val_c)
                        break

            sns.heatmap(frequency_matrix, cbar=first == 0,
                        cbar_ax=None if first else cbar_ax, vmin=0, vmax=1,
                        annot=np.array(heatmap_label2), fmt='',
                        annot_kws=my_annot_kws, linewidths=2,
                        xticklabels='', yticklabels='', cmap=own_cmap1,
                        ax=axes[j, i])
            # linewidths=.1
            first = first + 1
            if i == 0:
                axes[j, i].set_ylabel(short_name[element], fontsize=40)
            if j == len(ylabels)-1:
                axes[j, i].set_xlabel(xlab, fontsize=40)

        # add gray subplots to show the process that is not presented
        # in the element
        empty_plot = list(set(interesting_p) - set(xlabels.keys()))
        for emp in empty_plot:
            i = interesting_p.index(emp)
            sns.heatmap([[0.6]], cbar=False, vmin=0, vmax=1, xticklabels='',
                        yticklabels='', cmap="gist_gray", ax=axes[j, i])
            if i == 0:
                axes[j, i].set_ylabel(short_name[element], fontsize=40)
            if j == len(ylabels)-1:
                axes[j, i].set_xlabel(emp, fontsize=40)
    plt.savefig(output_folder + 'heatmapn.png', bbox_inches='tight')
    # plt.show()


def plot_totall_items(total_freq, output_folder):
    label = sorted(total_freq.keys(), key=total_freq.get, reverse=True)
    numbers = sorted(total_freq.values(), reverse=True)
    index = np.arange(len(label))
    plt.rc('axes', axisbelow=True)
    plt.grid(True, which='major', axis='y', linestyle='dashed')
    plt.bar(index, numbers)
    # plt.xlabel('Process Name', fontsize=5)
    # plt.ylabel('No of Occurrences', fontsize=5)

    plt.xticks(index, label, fontsize=18, rotation=20)
    plt.yticks(fontsize=18, rotation=0)
    # plt.title('Number of occurrences of process in PreFreeSurfer '
    #           'on 100 subjects')
    plt.savefig(output_folder+'frequency_plot.png')
    # plt.show()


def cmd_args_clustering(total_freq_union):
    p_options = {}
    for k in total_freq_union.keys():
        for p_name in total_freq_union[k].keys():
            for p_arg, val in total_freq_union[k][p_name].items():
                arg_splited = str(p_arg.strip(' ')).split(' ')
                diff_num, tota_num = val.split(' ')[0], val.split(' ')[-1]
                for i in arg_splited[1:]:

                    if p_name not in p_options.keys():
                        p_options[p_name] = {}

                    if i not in p_options[p_name].keys():
                        p_options[p_name][i] = (
                            "{} outof {}".format(int(diff_num), int(tota_num)))
                        # p_options[p_name][i] = int(diff_num) / int(tota_num)
                    else:
                        value = p_options[p_name][i]
                        tmp_n, total_n = (
                            value.split(' ')[0], value.split(' ')[-1])
                        p_options[p_name][i] = (
                            "{} outof {}".format(
                                int(diff_num)+int(tmp_n),
                                int(tota_num)+int(total_n))
                            )
    label_list = []
    color_list = []
    for key in p_options.keys():
        val_list = []
        for opt, nums in p_options[key].items():
            percentage = float(nums.split(' ')[0]) / float(nums.split(' ')[-1])
            p_options[key][opt] = percentage

        label_list.append(sorted(p_options[key].keys(), key=p_options[key].get,
                                 reverse=True)[:10])
        for ind, val in enumerate(sorted(p_options[key].values(),
                                         reverse=True)[:10]):
            if val > 0.9:
                val_list.append('#F75D59')  # red
            elif val == 0:
                val_list.append('#7BCCB5')  # green
            else:
                val_list.append('#FFF380')  # yellow
        color_list.append(val_list)
    # fig = go.Figure(data=[go.Table(header=dict(values=p_options.keys()),
    #                 cells=dict(values=label_list, fill_color=color_list))])
    # fig.write_image('tabelofoptions.png')
    # fig.show()


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
                        help='output folder to save the figures each '
                             'process-tree using graphviz')
    parser.add_argument('-p', '--plot',
                        help='plot barchart and heatmap of total differences')
    parser.add_argument('-g', '--graph',
                        help='make .dot and .png files for the graphs if '
                             'this parameter triggers')
    parser.add_argument('-t', '--threshold',
                        help='The threshold is defined as the minimum '
                             'distance required to separate clusters')

    args = parser.parse_args(args)
    input_folder = args.input_folder
    output_folder = args.output_folder

    # 1) get frequency of the processes with differences and
    # a list of input db files
    total_freq, sep_item_freq, db_file_list, pipe_proc2 = (
        get_item_frequency(input_folder))
    global pipe_proc
    pipe_proc = pipe_proc2
    if args.plot:
        # plot bar chart of totall differences
        interesting_p = sorted(total_freq.keys(), key=total_freq.get,
                               reverse=True)
        plot_totall_items(total_freq, output_folder)

        # 2) get the frequency of process with differences out of all the
        # interesting processes in pipeline and then make heatmap plot of them
        total_freq_100, total_freq_union = (
            ratio_of_diff_process(input_folder, interesting_p, sep_item_freq))
        plot_heatmap(total_freq_union, interesting_p, output_folder)

        # write total command line frequency as a json file
        with open(os.path.join(
                  output_folder, 'cmd_frequency.json'), 'w') as fp:
            json.dump(total_freq_union, fp, indent=4, sort_keys=True)

        # start to cluster command line arguments
        cmd_args_clustering(total_freq_union)

    # 3) start of hierarchical clustering of process trees
    if args.threshold:
        global le
        le = LabelEncoder()
        le.fit(db_file_list)
        clustering_process_trees(db_file_list, args.threshold, output_folder)

    # 4) make tree representation of diffrence process tree
    # see subj_clustering.orig.py section resurce
    # if args.graph:
    #     process_freq = {}
    #     subsets_dic = {}
    #     graph = Di('Graph',
    #                filename = os.path.join(output_folder, "Union_graph_hsv"),
    #                format='svg',
    #                strict=False)
    #     # graph.attr(compound=True)
    #     root = (WeirdNode("root"))
    #     represent_diff_tree(sqlite_file, root, 1, trees_dic, process_freq,
    #                         total_freq.keys(),
    #                         sep_item_freq, subsets_dic, graph)
    #     graph.render()


if __name__ == '__main__':
    main()
