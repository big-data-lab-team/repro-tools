#!/usr/bin/env python

"""verifyFiles.py.

Script to check whether the output files generated across
subject folders in different conditions are the same or not.

"""

import os
import sys
import subprocess
import argparse
import textwrap
import hashlib
import operator
import logging
import csv
import sqlite3
import re
import pandas as pd
import random
import json


# Returns a dictionary where the keys are the paths in 'directory'
# (relative to 'directory') and the values are the os.stat objects
# associated with these paths. By convention, keys representing
# directories have a trailing '/'.
def get_dir_dict(directory, exclude_items):
    result_dict = {}
    for root, dirs, files in os.walk(directory):
        if exclude_items is not None:
            dirs[:] = [d for d in dirs if d not in exclude_items]
            # To eliminate the files listd in exclude items file.
            # Condition below checks relative file path as well as file names.
            files[:] = [f for f in files if f not in exclude_items and
                        os.path.join(root, f)
                        .replace(os.path.join(directory+"/"), "")
                        not in exclude_items]
            for file_name in files:
                if not exclude_items or (file_name not in exclude_items):
                    abs_file_path = os.path.join(root, file_name)
                    rel_path = abs_file_path.replace(os.path
                                                     .join(directory+"/"), "")
                    # if '/' in rel_path and \
                    #    directory.split('/')[-1] in rel_path:
                    #     rel_path = rel_path.replace(directory.split('/')[-1],
                    #                                 "subject_name")
                    result_dict[rel_path] = os.stat(abs_file_path)
    return result_dict


# Returns a dictionary where the keys are the directories in
# 'condition_dir' and the values are the directory dictionaries (as
# returned by get_dir_dict) associated to these directories.
def get_condition_dict(condition_dir, exclude_items):
    condition_dict = {}
    subject_names_list = []
    subject_names_list[:] = [subject_name for subject_name in
                             os.listdir(condition_dir)]
    if exclude_items is not None:
        subject_names_list[:] = [subject_name for subject_name in
                                 subject_names_list if
                                 subject_name not in exclude_items]
    for subject_name in subject_names_list:
        subject_dir_path = os.path.join(condition_dir, subject_name)
        if os.path.isdir(subject_dir_path):
            condition_dict[subject_name] = get_dir_dict(subject_dir_path,
                                                        exclude_items)
    return condition_dict


# Returns a dictionary where the keys are the names in
# 'condition_names' and the values are the corresponding condition
# dictionaries (as returned by get_condition_dict)
def get_conditions_dict(condition_names, root_dir, exclude_items):
    conditions_dict = {}
    if exclude_items is not None:
        condition_names[:] = [condition for condition in condition_names if
                              condition not in exclude_items]
    for condition in condition_names:
        conditions_dict[condition] = get_condition_dict(os.path.join(root_dir,
                                                        condition),
                                                        exclude_items)

    # Get the intersection files between a subject in two conditions
    if len(condition_names) == 2:
        subj_name = (list(conditions_dict[
                     list(conditions_dict.keys())[0]].keys())[0])
        first_dic = list(conditions_dict.keys())[1]
        sec_dic = list(conditions_dict.keys())[0]
        intersections = (set(conditions_dict[first_dic][subj_name]) &
                         set(conditions_dict[sec_dic][subj_name]))

        for key, val in conditions_dict.items():
            for k2, val2 in val.items():
                for k in list(val2.keys()):
                    if k not in intersections:
                        del conditions_dict[key][k2][k]

    return conditions_dict


# Returns a list where each element is a line in 'file_name'
def read_file_contents(file_name):
    if file_name is None:
        return None
    with open(file_name, 'r') as infile:
        data = infile.read()
        directory_list = data.splitlines()
    return directory_list


# Parses the metrics from the metrics file
def read_metrics_file(file_name):
    metrics = {}
    if file_name is None:
        return metrics
    with open(file_name, 'r') as csvfile:
        linereader = csv.reader(csvfile, delimiter=',')
        for row in linereader:
            metric = {}
            metric['name'] = row[0]
            metric['extension'] = row[1]
            metric['command'] = row[2]
            metric['output_file'] = row[3]
            metrics[metric['name']] = metric
    return metrics


# Returns the checksum of path 'path_name'
def checksum(path_name):
    hasher = hashlib.md5()
    assert((os.path.exists(path_name)),
           "File {} doesn't exist".format(path_name))
    if os.path.isfile(path_name):
        md5_sum = file_hash(hasher, path_name)
    elif os.path.isdir(path_name):
        md5_sum = directory_hash(hasher, path_name.encode("utf-8"))
    return md5_sum


# Method file_hash is used for generating md5 checksum of a file
# Input parameters: file name and hasher
def file_hash(hasher, file_name):
    file_content = open(file_name, 'rb')
    while True:
        read_buffer = file_content.read(2**20)
        if len(read_buffer) == 0:
            break
        hasher.update(read_buffer)
    file_content.close()
    return hasher.hexdigest()


# Method directory_hash collects the directory and file names from
# the directory given as input.
# Checksum is created on the basis of filenames and directories present
# in the file input directory.
# #Input parameters: hashed content , path
def directory_hash(hasher, dir_path):
    if os.path.isdir(dir_path):
        for entry in sorted(os.listdir(dir_path)):
            hasher.update(entry)
    return hasher.hexdigest()


# Stops the execution if not all the subjects of all the conditions
# have the same list of files
def check_files(conditions_dict):
    path_names = set()
    for condition in conditions_dict:
        for subject in conditions_dict[condition]:
            path_names.update(conditions_dict[condition][subject].keys())
    for path_name in path_names:
        for condition in conditions_dict.keys():
            for subject in conditions_dict[condition].keys():
                if path_name not in conditions_dict[condition][subject].keys():
                    # log_warning("File \"" + path_name +
                    #            "\" is missing in subject \"" + subject +
                    #            "\" of condition \"" + condition + "\".")
                    if subject in path_name:
                        del conditions_dict[condition][subject][path_name]


def txt_check_file(abs_path_c, abs_path_d):
    cmd = 'diff -y --suppress-common-lines {} {}'.format(abs_path_c,
                                                         abs_path_d)
    out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).communicate()
    list_of_keys = ["mri_segreg --seed 1234", "regfile", "outregfile",
                    "outfile", "cd", "TimeStamp", "hostname", "movvol",
                    "created by ", "filename", "creationtime", "CreationTime",
                    "SegVolFileTimeStamp", "OptimizationTime", "SUBJECTS_DIR",
                    "transform file", "<![CDATA[", "PVVolFileTimeStamp",
                    "InVolFileTimeStamp", "generating_program",
                    "AnnotationFileTimeStamp", "cmdline", "surfacefile ",
                    "cmd[0]: ", "cmd[1]: ", "cmd[2]: ", "cmd[3]: ", "cmd[4]: ",
                    "cmd[5]: "]
    for line in out.splitlines():
        flag = False
        for key in list_of_keys:
            if key in line:
                flag = True
                break
        if flag:
            continue
        return False
    return True


def mri_check_file(abs_path_c, abs_path_d):
    # mri_diff
    cmd = 'mri_diff {} {}'.format(abs_path_c, abs_path_d)
    out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).communicate()
    if 'Volumes differ' in out:
        return False
    return True


def mris_check_file(abs_path_c, abs_path_d):
    # mris_diff
    cmd = 'mris_diff {} {}'.format(abs_path_c, abs_path_d)
    out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).communicate()
    if 'Surfaces are the same' in out:
        return True
    elif 'Surfaces differ' in out:
        return False


def lta_check_file(abs_path_c, abs_path_d):
    # lta_diff
    cmd = 'lta_diff {} {}'.format(abs_path_c, abs_path_d)
    out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).communicate()
    for line in out.splitlines():
        if line == '0':
            return True
        elif line == '1':
            return False


def check_file_data(abs_path_c, abs_path_d):

    mri_list = ['.mgz', '.gz', '.volume', '.sulc', '.K', '.H', '.area',
                '.curv', '.thickness', '.crv']
    mri_list2 = ['.area.deformed', '.area.prehires', '.area.pial',
                 '.curv.deformed', '.curv.pial', '.curv.prehires',
                 '.thickness.postT2.pass1', '.thickness.postT2.pass2',
                 '.thickness.preT2.pass1', '.thickness.preT2.pass2',
                 '.area.pial.postT2.pass1', '.area.pial.postT2.pass2',
                 '.curv.pial.postT2.pass1', '.curv.pial.postT2.pass2']
    mris_list = ['.nofix', '.reg', '.smoothwm', '.sphere', '.orig',
                 '.inflated', '.hires', '.white']
    mris_list2 = ['.pial', '.pial.preT2.pass1', '.pial.preT2.pass2',
                  '.pial.postT2.pass1', '.pial.postT2.pass2',
                  '.pial.postT2.pass1.conformed', '.white.prehires',
                  '.white.deformed']
    lta_list = ['.lta']
    txt_list = ['.stats', '.sum', '.gii']

    if os.path.splitext(abs_path_c)[1] in mri_list:
        return mri_check_file(abs_path_c, abs_path_d)
    if os.path.splitext(abs_path_c)[1] in mris_list:
        return mris_check_file(abs_path_c, abs_path_d)
    if os.path.splitext(abs_path_c)[1] in lta_list:
        return lta_check_file(abs_path_c, abs_path_d)
    if os.path.splitext(abs_path_c)[1] in txt_list:
        return txt_check_file(abs_path_c, abs_path_d)
    for ext in mri_list2:
        if abs_path_c.endswith(ext):
            return mri_check_file(abs_path_c, abs_path_d)
    for ext in mris_list2:
        if abs_path_c.endswith(ext):
            return mris_check_file(abs_path_c, abs_path_d)
    return False


# Returns a dictionary where the keys identifies two conditions
# (e.g. "condition1 vs condition2") and the values are dictionaries
# where the keys are path names common to these two conditions and the
# values are the number of times that this path differs among all
# subjects of the two conditions.
# For instance:
#  {'condition1 vs condition2': {'c/c.txt': 0, 'a.txt': 2}}
#  means that 'c/c.txt' is identical for all subjects in conditions
# condition1 and condition2 while 'a.txt' differs in two subjects.
def n_differences_across_subjects(conditions_dict,
                                  root_dir,
                                  metrics,
                                  checksums_from_file_dict,
                                  checksum_after_file_path,
                                  check_corruption,
                                  sqlite_db_path,
                                  track_processes, comp):
    # For each pair of conditions C1 and C1
    product = ((i, j) for i in conditions_dict.keys()
               for j in conditions_dict.keys())
    diff = {}  # Will be the return value
    # Dictionary metric_values_subject_wise holds the metric values mapped to
    # individual subjects. This helps us identify the metrics values and
    # associate it with individual subjects.
    path_names = list(list(conditions_dict.values())[0].values())[0].keys()
    # dictionary_checksum is used for storing the computed checksum values
    # and to avoid computing the checksums for the files multiple times
    dictionary_checksum = {}
    # dictionary_executables is used for tracking the files that we have
    # already found the executables for
    dictionary_executables = {}
    dictionary_processes = {}
    # Initialize sqlite connection
    if sqlite_db_path:
        try:
            conn = sqlite3.connect(sqlite_db_path)
        except sqlite3.Error as e:
            log_error(e)
    # Go through all pairs of conditions
    for c, d in product:
        #  Makes sure that pairs are not ordered,
        # i.e. {a,b} and {b,a} are the same
        if comp:
            if c >= d:
                continue
        else:
            if c > d:
                continue
        # ~ key = c+" vs "+d
        key = "condition1 vs condition2"
        diff[key] = {}
        diff[key]['conditions'] = [c, d]
        diff_files = {}
        diff[key]['files'] = diff_files
        # if c and d both start with x-RUN-y (same x, different
        # y), then assume that they are different runs from the
        # same condition. In this case, if there are differences
        # for a given file name below, the reprozip trace should
        # be inspected to determine the executable that created
        # such inter-run differences in the same condition. Also,
        # print a log_info saying "Identified c1 and c2 as two
        # different runs of the same condition".
        is_intra_condition_run = False
        # Adding variable for holding the substituted name
        pattern = re.compile('.*-RUN-[0-9]*')
        if pattern.match(c) and pattern.match(d):
            condition_c = c.split("-")
            condition_d = d.split("-")
            # Checking if the runs are intra runs on the same
            # condition(Operating System).
            if (condition_c and condition_d) and \
               (condition_c[0] == condition_d[0]):
                log_info("Identified " + c + " and " + d +
                         " as two different runs of the same condition")
        is_intra_condition_run = True
        for file_name in path_names:
            diff_files[file_name] = {}
            diff_files[file_name]['subjects'] = {}
            diff_files[file_name]['sum'] = {}
            for subject in conditions_dict[c].keys():
                diff_files[file_name]['subjects'][subject] = {}
                # diff_files[file_name]['subjects'][subject]['mtime'] = (
                #        conditions_dict[c][subject][file_name].st_mtime)
        for file_name in path_names:
            file_dict = diff_files[file_name]
            file_dict['sum']['checksum'] = 0
            if 'subject_name' in file_name:
                file_name = file_name.replace('subject_name', subject)
            for subject in conditions_dict[c].keys():
                # Track the processes which created the files using
                # reprozip trace.
                if track_processes and sqlite_db_path and \
                   file_name not in dictionary_processes:
                    executable = get_executable_details(conn, sqlite_db_path,
                                                        file_name)
                    if diff_files.get('executable') is None:
                        diff_files['executable'] = executable
                    assert(diff_files['executable'] == executable), (
                           "File {} is produced by different executables"
                           .format(file_name))
                # Now check the differences in file_name
                # Here we assume that both conditions will have
                # the same set of subjects
                files_are_different = False
                abs_path_c = os.path.join(root_dir, c, subject, file_name)
                abs_path_d = os.path.join(root_dir, d, subject, file_name)
                if checksums_from_file_dict:
                    if (checksums_from_file_dict[c][subject][file_name] !=
                       checksums_from_file_dict[d][subject][file_name]):
                        files_are_different = True
                    elif (conditions_dict[c][subject][file_name].st_size
                          != conditions_dict[d][subject][file_name].st_size):
                        files_are_different = True
                else:
                    # Computing the checksum if not present in the dictionary
                    # and adding it to the dictionary to avoid multiple
                    # checksum computation.
                    for filename in {abs_path_d, abs_path_c}:
                        if filename not in dictionary_checksum:
                            dictionary_checksum[filename] = checksum(filename)
                    if (dictionary_checksum[abs_path_c] !=
                       dictionary_checksum[abs_path_d]):
                        files_are_different = True

                diff_files[file_name]['subjects'][subject]['checksum'] = 0
                diff_files[file_name]['subjects'][subject]['MD5'] = (
                    dictionary_checksum[abs_path_c])

                if not files_are_different:
                    continue
                if check_file_data(abs_path_c, abs_path_d):
                    continue
                # Files are different
                diff_files[file_name]['subjects'][subject]['MD5-cond1'] = (
                    dictionary_checksum[abs_path_c])
                diff_files[file_name]['subjects'][subject]['MD5-cond2'] = (
                    dictionary_checksum[abs_path_d])
                diff_files[file_name]['subjects'][subject]['checksum'] = 1
                diff_files[file_name]['sum']['checksum'] += 1

                # Below condition is making sure that the checksums
                # are getting read from the file.Also that we are
                # not computing the checksum of the checksums-after file.
                if check_corruption and checksums_from_file_dict and \
                   checksum_after_file_path not in file_name:
                    # If the checksum of the file computed locally is
                    # different from the one in the file, the file
                    # got corrupted and hence throw error.
                    if (checksum(abs_path_c) !=
                       checksums_from_file_dict[c][subject][file_name]):
                        log_error("Checksum of\"" + abs_path_c +
                                  "\"in checksum file is different from "
                                  "what is computed here.")
                    # If the checksum of the file computed locally is different
                    # from the one in the file, the file got corrupted
                    # and hence throw error.
                    if (checksum(abs_path_d) !=
                       checksums_from_file_dict[d][subject][file_name]):
                        log_error("Checksum of\"" + abs_path_d +
                                  "\"in checksum file is different from "
                                  "what is computed here.")
                metrics_to_evaluate = get_metrics(metrics, file_name)
                if len(metrics_to_evaluate) != 0:
                    for metric in metrics.values():
                        if not file_name.endswith(metric['extension']):
                            continue
                        try:
                            log_info("Computing the metrics for the file:" +
                                     " " + file_name + " " + "in subject" +
                                     " " + subject)
                            log_info(file_name + " " + c + " " + d + " " +
                                     subject + " " + metric['command'])
                            diff_value = float(run_command(metric['command'],
                                               file_name, c, d, subject,
                                               root_dir))
                            (diff_files[file_name]['subjects'][subject]
                             [metric['name']]) = diff_value
                            diff_files[file_name]['sum'][metric['name']] += (
                                                                  diff_value)
                        except ValueError as e:
                            log_error("Result of metric execution could not "
                                      "be cast to float" + " " +
                                      metric['command'] + " " + file_name +
                                      " " + c + " " + d + " " + subject +
                                      " " + root_dir)
    if sqlite_db_path:
        conn.close()
    return diff


# Method get_executable_details is used for finding out the details of
# the processes that created or modified the specified file.
# TODO Intra condition run is not taken into account while the executable
# details are getting written to the file
def get_executable_details(conn, sqlite_db_path, file_name):
    sqlite_cursor = conn.cursor()
    # opened_files table has a column named MODE
    # The definition of the mode values are as described below
    # FILE_READ =1
    # FILE_WRITE=2
    # FILE_WDIR=4
    # FILE_STAT=8
    # FILE_LINK=16
    sqlite_cursor.execute('SELECT DISTINCT executed_files.name,'
                          'executed_files.argv,executed_files.envp,'
                          'executed_files.timestamp,executed_files.workingdir'
                          ' from executed_files INNER JOIN opened_files where'
                          ' opened_files.process = executed_files.process and'
                          ' opened_files.name like ? and opened_files.mode=2 '
                          'and opened_files.is_directory=0',
                          ('%/'+file_name, ))
    data = sqlite_cursor.fetchall()
    sqlite_cursor.close()
    executable_details_list = []
    if data:
        for row in data:
            # Adding to a list, all the processes and the details
            # which operated on the given file
            executable_details_list.append(row)
    return executable_details_list


# Returns the list of metrics associated with a given file name, if any
def get_metrics(metrics, file_name):
    matching_metrics = []
    for metric in metrics.values():
        if file_name.endswith(metric['extension']):
            matching_metrics.append(metric)
    return matching_metrics


# Executes the following command:
# 'command condition1/subject_name/file_name condition2/subject_name/file_name'
# and returns the stdout if and only if command was successful
def run_command(command, file_name, condition1, condition2,
                subject_name, root_dir):
    command_string = (command + " " +
                      os.path.join(root_dir, condition1, subject_name,
                                   file_name) + " " +
                      os.path.join(root_dir, condition2, subject_name,
                                   file_name) + " " + "2>/dev/tty")
    process = subprocess.Popen(command_string,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    return_value = process.wait()
    print(process.stdout.read())
    print(process.stderr.read())
    assert(code == 0), "Command failed"
    if return_value != 0:
        log_error(str(return_value)+" " + "Command " + command +
                  " failed (" + command_string + ").")
    return output


# Method read_checksum_from_file gets the file path containing the checksum
# and the file name. It reads the content line by line and if a match is found,
# it adds the file name as key and checksum as the value and returns
# dictionary after the file gets read.
def read_checksum_from_file(checksums_after_file_path):
    checksum_from_file_dict = {}
    with open(checksums_after_file_path) as file:
        for line in file:
            if (len(line.split(' ', 1)) == 2) and '/' in line:
                filename = ((line.split(' ', 1)[1]).strip())
                filename = filename.split('/', 2)[2]
                checksum_from_file_dict[filename] = (
                                            (line.split(' ', 1)[0]).strip())
    return checksum_from_file_dict


# Method get_conditions_checksum_dict creates a dictionary containing ,
# the dictionaries under different condition with the condition as
# the key and subject folder dictionaries as the value.
def get_conditions_checksum_dict(conditions_dict, root_dir,
                                 checksum_after_file_path):
    conditions_checksum_dict = {}
    conditions = conditions_dict.keys()
    subjects = list(conditions_dict.values())[0].keys()
    for condition in conditions:
        conditions_checksum_dict[condition] = get_condition_checksum_dict(
            condition, root_dir, subjects, checksum_after_file_path)
    return conditions_checksum_dict


# Method get condition checksum dictionary, creates a dictionary with
# subject as key, and associated files and checksums as values.
def get_condition_checksum_dict(condition, root_dir, subjects,
                                checksum_after_file_path):
    condition_checksum_dict = {}
    for subject in subjects:
        condition_checksum_dict[subject] = read_checksum_from_file(
            os.path.join(root_dir, condition, subject,
                         checksum_after_file_path))
    return condition_checksum_dict


# # Write column_index text file of the matrix
# def matrix_column(bDiff, condition, condition_id, column_index):
#     column_index.write(str(condition_id))
#     column_index.write(";")
#     column_index.write(str(condition))
#     column_index.write("\n")


# # Write the text file of matrix according to the define conditions for it
# def matrix_differences(bDiff, condition, subject, path, r, c, mode,
#                        differences):
#     differences.write(str(r))
#     differences.write(";")
#     differences.write(str(c))
#     differences.write(";")
#     differences.write(str(bDiff[condition][subject][path]))
#     if mode is True:
#         differences.write(";")
#         differences.write(str([bDiff[condition][subject]
#                               ['mtime_files_list'].index(t) for t in
#                               bDiff[condition][subject]['mtime_files_list']
#                               if t[0] == path])[1:-1])  # file_index
#     differences.write("\n")


# # Write row_index text file of the matrix
# def matrix_row(bDiff, subject, path, r, mode, row_index):
#     row_index.write(str(r))
#     row_index.write(";")
#     if mode is False:
#         row_index.write(str(subject))
#         row_index.write(";")
#     row_index.write(str(path))
#     row_index.write("\n")


# # Write binary_difference_matrix
# def matrix_text_files(bDiff, conditions_dict, fileDiff,
#                       mode, condition_pairs):
#     r = 0
#     c = 0
#     if mode is True:
#         file_name = "_2D_"+str(condition_pairs)
#         file_name = file_name.replace(' ', '').replace("/", "_")
#     else:
#         file_name = "_3D"
#     row_index = open(fileDiff + file_name + "_row_index.txt", "w+")
#     column_index = open(fileDiff + file_name + "_column_index.txt", "w+")
#     differences = open(fileDiff + file_name + "_differences.txt", "w+")
#     if mode is True:
#         for subject in bDiff[list(bDiff.keys())[0]].keys():
#             matrix_column(bDiff, subject, c, column_index)
#             for path in list(list(conditions_dict.values())[0]
#                              .values())[0].keys():
#                 matrix_differences(bDiff, condition_pairs, subject, path,
#                                    r, c, mode, differences)
#                 matrix_row(bDiff, subject, path, r, mode, row_index)
#                 r += 1
#             r = 0
#             c += 1
#     else:
#         for condition in bDiff.keys():
#             matrix_column(bDiff, condition, c, column_index)
#             for subject in bDiff[list(bDiff.keys())[c]].keys():
#                 for path in list(list(conditions_dict.values())[c]
#                                  .values())[c].keys():
#                     matrix_differences(bDiff, condition, subject, path,
#                                        r, c, mode, differences)
#                     matrix_row(bDiff, subject, path, r, mode, row_index)
#                     r += 1
#             r = 0
#             c += 1
#     return (row_index, column_index, differences)


# def pretty_string(diff_dict, conditions_dict):
#     return json.dumps(diff_dict, indent=4, sort_keys=True)


# Returns a string containing a 'pretty' matrix representation of the
# dictionary returned by n_differences_across_subjects
# Method check_subjects checks if the subject_folders under different
# conditions are the same. If not , it stops the execution of the script.
def check_subjects(conditions_dict):
    subject_names = set()
    for condition in conditions_dict.keys():
        subject_names.update(conditions_dict[condition].keys())
        # Iterate over each soubject in every condition and stop the execution
        # if some subject is missing
        for subject in subject_names:
            for condition in conditions_dict.keys():
                if subject not in conditions_dict[condition].keys():
                    log_error("Subject \"" + subject +
                              "\" is missing under condition \"" +
                              condition + "\".")


# # function to write the individual file detials to files
# def write_filewise_details(metric_values_subject_wise,
#                            metric_name, file_name):
#     log_info(metric_name +
#              " values getting written to subject wise into a csv file: " +
#              file_name)
#     with open(file_name, 'wb') as f:
#         writer = csv.writer(f)
#         for item in metric_values_subject_wise[metric_name]:
#             for subject in metric_values_subject_wise[metric_name][item]:
#                 for file_name in (metric_values_subject_wise[metric_name]
#                                   [item][subject]):
#                     writer.writerow([item, subject, file_name,
#                                      metric_values_subject_wise[metric_name]
#                                      [item][subject][file_name]])


# Logging functions
def log_info(message):
    logging.info(message)


def log_error(message):
    logging.error("ERROR: " + message)
    sys.exit(1)


def log_warning(message):
    logging.warning("WARNING: "+message)


def check_file(parser, x):
    if x is None:
        parser.error('File is None')
    if True:  # os.path.exists(x):
        return x
    print('cwd: {}'.format(os.getcwd()))
    parser.error("File does not exist: {}".format(x))


def main(args=None):
    parser = argparse.ArgumentParser(description="verifyFiles.py",
                                     formatter_class=argparse
                                     .RawTextHelpFormatter)
    parser.add_argument("file_in",
                        help=textwrap.dedent('''
                        Input the text file containing the path
                        to the condition folders
                        Each directory contains subject folders containing
                        subject-specific and modality-specific data
                        categorirzed into different subdirectories.
                    Sample:
                    Format : <subject_id>/unprocessed/3T/
                    Unprocessed data for example subject 100307 unpacks
                    to the following directory structure:
                    100307/unprocessed/3T/
                    100307_3T.csv
                        Diffusion
                        rfMRI_REST1_LR
                        rfMRI_REST1_RL
                        rfMRI_REST2_LR
                        rfMRI_REST2_RL
                        T1w_MPR1
                        T2w_SPC1
                    ....
                    ...
                        These subdirectories will be processed under
                        different conditions.
                        Conditions refer to the operating system on
                        which the process is ran or the version of
                        the pipeline which is used to process the data.
                        An example would be a directory containing
                        the files processed using CentOS6 operating
                        system and PreFreeSurfer version 5.0.6
                    Sample of the input file
                        /home/$(USER)/CentOS6.FSL5.0.6
                        /home/$(USER)/CentOS7.FSL5.0.6
                        Each directory will contain subject folders
                        like 100307,100308 etc'''),
                        type=lambda x: check_file(parser, x))

    parser.add_argument("result_file",
                        help='JSON file containing the results')
    parser.add_argument("-c", "--checksumFile",
                        type=lambda x: check_file(parser, x),
                        help="Reads checksum from files. "
                             "Doesn't compute checksums locally")
    parser.add_argument("-m", "--metricsFile",
                        type=lambda x: check_file(parser, x),
                        help="CSV file containing metrics definition."
                             "Every line contains 4 elements: metric_name,"
                             "file_extension,command_to_run,"
                             "output_file_name")
    parser.add_argument("-e", "--excludeItems",
                        type=lambda x: check_file(parser, x),
                        help="The list of items to be ignored while "
                             "parsing the files and directories")
    parser.add_argument("-k", "--checkCorruption",
                        help="If this flag is kept 'TRUE', it checks "
                             "whether the file is corrupted")
    parser.add_argument("-s", "--sqLiteFile",
                        type=lambda x: check_file(parser, x),
                        help="The path to the sqlite file which is used "
                             "as the reference file for identifying the "
                             "processes which created the files")
    parser.add_argument("-x", "--execFile",
                        help="Writes the executable details to a file")
    parser.add_argument("-t", "--trackProcesses",
                        help="Writes all the processes that create "
                             "an nii file is written into file name "
                             "mentioned after the flag")
    parser.add_argument("-r", "--one_condition",
                        type=lambda x: check_file(parser, x),
                        help="List files and thier MD5 values  "
                             "on one condition without any comparison")
    args, params = parser.parse_known_args(args)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')
    root_dir = os.path.dirname(os.path.abspath(args.file_in))
    # logger_ = logging.getLogger()
    # logger_.disabled = True
    # logger_.propagate = False
    comp = True
    if args.one_condition:
        comp = False
        abs_path_cond = os.path.abspath(args.one_condition)
        root_direct = os.path.join(root_dir+"/")
        conditions_list = [abs_path_cond.replace(root_direct, "")]
    else:
        conditions_list = read_file_contents(args.file_in)

    log_info("Walking through files...")
    # exclude_items is a list containing the folders and files which
    # should be ignored while traversing through the directories
    exclude_items = read_file_contents(args.excludeItems)
    conditions_dict = get_conditions_dict(conditions_list, root_dir,
                                          exclude_items)
    log_info("Checking if subject folders are missing in any condition...")
    check_subjects(conditions_dict)
    log_info("Checking if files are missing in any subject of "
             "any condition...")
    check_files(conditions_dict)
    log_info("Reading the metrics file...")
    metrics = read_metrics_file(args.metricsFile)
    log_info("Computing differences across subjects...")
    checksums_from_file_dict = {}
    if args.checksumFile:
        log_info("Reading checksums from files...")
        checksums_from_file_dict = get_conditions_checksum_dict(
                                        conditions_dict, root_dir,
                                        args.checksumFile)
    # Checking whether sqlite file path alone or executable file name
    # alone is given. In case only one is given, throw error.
    if (args.sqLiteFile and args.execFile is None) or \
       (args.execFile and args.sqLiteFile is None):
        log_error("Input the SQLite file path and the name of the file "
                  "to which the executable details should be saved")
    # Differences across subjects needs the conditions dictionary,
    # root directory, checksums_from_file_dictionary,
    # and the file checksumFile,checkCorruption and the path to
    # the sqlite file. diff,metric_values,dictionary_executables,
    # dictionary_processes= n_differences_across_subjects(conditions_dict,
    # root_dir,metrics, checksums_from_file_dict,args.checksumFile,
    # args.checkCorruption,args.sqLiteFile)i
    diff = n_differences_across_subjects(conditions_dict, root_dir,
                                         metrics, checksums_from_file_dict,
                                         args.checksumFile,
                                         args.checkCorruption,
                                         args.sqLiteFile,
                                         args.trackProcesses,
                                         comp)
    with open(args.result_file, 'w') as f:
        f.write(json.dumps(diff, indent=4, sort_keys=True))


if __name__ == '__main__':
    main()
