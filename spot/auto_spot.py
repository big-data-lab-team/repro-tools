#!/usr/bin/python

"""Spot-tool.

This is the automation of labeling pipeline processes:
(1) Running pipeline in condition 1 using reprozip trace.
(2) Running pipeline in condition 1 to capture intermediate files.
(3) Running pipeline in condition 2 to label all the processes.
"""

import argparse
import sys
import re
import os
import os.path as op
import logging
import json
import shutil
import boutiques
import docker
import sqlite3
from spot.verify_files import main as verify_files
from spot.spottool import main as spot


# The procedure of labeling pipeline is as following steps:
# (1) Run pipeline on Condition 1 (Centos6) to get the result files and
# process tree
# (2) Run pipeline on Condition 1 to capture temporary and multi-write files
# (3) Run pipeline on Condition 2 (Centos7) to label process graph

def log_info(message):
    logging.info("INFO: " + message)


def pipeline_executor(descriptor, invocation):
    with open(descriptor, 'r') as jsonFile:
        data = json.load(jsonFile)
    # Check that Boutiques descriptor has a Docker container
    if data["container-image"]["type"] != 'docker':
        sys.exit("Container must be a docker image!")
    print("Docker image: {}".format(data["container-image"]["image"]))

    try:
        print("Launching Boutiques tool")
        output_object = boutiques.execute("launch", '-x',
                                          descriptor, invocation)
    except SystemExit as e:
        return(e.code)
    print(output_object)
    if(output_object.exit_code):
        sys.exit("Pipeline execution failed.")


# Returns the written files (W)
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
            or name like '%/usr/local/src/tools/%'
            or name like '%/bin/grep%')
            and name <> '/usr/local/src/fsl/bin/imtest'
            and name <> '/usr/local/src/fsl/bin/imcp'
            '''
    execp_cursor.execute(process_name_query)
    return execp_cursor.fetchall()


def make_modify_script(spot_data_path, lst_proc, wrapper_script):
    cmd_file = open(op.join(spot_data_path, 'cmd.sh'), 'w+')
    cmd_file.write('#!/usr/bin/env bash \n')
    cmd_list = []
    cwd = op.abspath(os.getcwd())
    list_ = []
    if type(lst_proc) == dict:
        for cmd in lst_proc.keys():
            # if op.basename(cmd.split('\x00')[0]) != "cp":
            list_.append(cmd.split('\x00')[0])
    else:
        for cmd in lst_proc:
            # if op.basename(cmd[0]) != "cp":
            list_.append(cmd[0])
        list_.append('/usr/bin/cp')

    for ind, pipeline_command in enumerate(list_):
        if pipeline_command not in cmd_list:
            cmd_list.append(pipeline_command)
            # Make a copy of process to backup folder if doesn't exist
            backup_path = op.join(spot_data_path,
                                  'backup_scripts',
                                  pipeline_command.strip('/'))
            backup_path_all = op.join(
                                       spot_data_path,
                                       'backup_scripts',
                                       pipeline_command.split('/')[-1:][0])

            if 'recon-all' in pipeline_command:
                continue

            if not op.exists(backup_path):
                if not op.exists(op.dirname(backup_path)):
                    os.makedirs(op.dirname(backup_path))
                if pipeline_command == '/usr/bin/cp':
                    cmd_file.write('cp ' + op.join(spot_data_path,
                                   'license.txt ')
                                   + ' /usr/local/src/freesurfer/ ' + '\n')
                    cmd_file.write('cp ' + '`which '+pipeline_command + '` '
                                   + op.join(spot_data_path, 'backup_scripts/')
                                   + '\n')

                cmd_file.write('cp ' + '`which '+pipeline_command + '` '
                               + backup_path + '\n')
                cmd_file.write('cp ' + '`which '+pipeline_command + '` '
                               + backup_path_all + '\n')
                cmd_file.write('cp ' + wrapper_script + ' `which ' +
                               pipeline_command + '`' + '\n')

                if 'wb_command' in pipeline_command:
                    if not op.exists(op.join(
                                         spot_data_path, 'backup_scripts',
                                         'usr/local/src/freesurfer/mni/share')
                                     ):
                        if not op.exists(op.join(
                                             spot_data_path,
                                             'backup_scripts',
                                             'usr/local/src/freesurfer/mni')
                                         ):
                            os.makedirs(op.join(
                                                spot_data_path,
                                                'backup_scripts',
                                                'usr/local/src/freesurfer/mni')
                                        )
                        cmd_file.write(
                            'cp -r /usr/local/src/freesurfer/mni/share ' +
                            op.join(
                                spot_data_path, 'backup_scripts',
                                'usr/local/src/freesurfer/mni/') +
                            '\n')
                        cmd_file.write(
                            'chmod -R 757 ' + op.join(
                                spot_data_path,
                                'backup_scripts',
                                'usr/local/src/freesurfer/mni/share') +
                            '\n')

                    cmd_file.write(
                        'cp -r /usr/local/src/tools/workbench/libs_rh_linux64 '
                        + op.join(
                            spot_data_path, 'backup_scripts',
                            'usr/local/src/tools/workbench/libs_rh_linux64') +
                        '\n')
                    cmd_file.write(
                        'chmod -R 757 ' +
                        op.join(
                            spot_data_path,
                            'backup_scripts',
                            'usr/local/src/tools/workbench/libs_rh_linux64'
                            ) +
                        '\n')


def modify_docker_image(descriptor, spot_data_path, tag_name, from_path,
                        to_path, process_list):
    with open(descriptor, 'r') as jsonFile:
        data = json.load(jsonFile)
    image_name = data["container-image"]["image"]
    client = docker.from_env()
    # print("Running command: {}".format(cmd_list))
    # ~ cwd = op.abspath(op.join(os.getcwd(), '../..'))
    cwd = op.abspath(os.getcwd())
    cmd_file_path = op.join(spot_data_path, 'cmd.sh')
    # with open(cmd_file_path, 'r') as cmdFile:
    #    cmd = cmdFile.readlines()
    container = client.containers.run(image_name,
                                      command='sh ' + cmd_file_path,
                                      volumes={cwd:
                                               {'bind': cwd,
                                                'mode': 'rw'}},
                                      environment=(["PYTHONPATH=$PYTHONPATH:"
                                                   + cwd,
                                                   "SPOT_TOOLS_PATH=" +
                                                    os.getcwd(),
                                                    "SPOT_OUTPUT_PATH=" +
                                                    spot_data_path,
                                                    "PROCESS_LIST=" +
                                                    process_list,
                                                    "FROM_PATH=" +
                                                    from_path,
                                                    "TO_PATH=" +
                                                    to_path]),
                                      working_dir=cwd,
                                      detach=True)
    container.logs()
    container.wait()
    new_img_name = image_name.split(':')[0] + "_" + tag_name
    image = container.commit(new_img_name)
    json_file_editor(descriptor, new_img_name, 'image')
    # ~ data["container-image"]["image"] = new_img_name
    # ~ with open(descriptor, 'w+') as jsonFile:
    # ~ json.dump(data, jsonFile)


def json_file_editor(descriptor, new_param=None, act=None):
    with open(descriptor, 'r') as jsonFileR:
        data = json.load(jsonFileR)
    if act == "image":
        data["container-image"]["image"] = new_param
    elif act is None:
        return data["container-image"]["image"]
        # ~ data["total_multi_write_proc"] = {}
        # ~ data["total_temp_proc"] = {}
        # data = {}
    with open(descriptor, 'w+') as jsonFileW:
        json.dump(data, jsonFileW, indent=4, sort_keys=True)


def classify_process(verify_cond, exclude_items, output_dir, sqlite_db,
                     spot_classify_file, reference_cond):
    # (2) Get the difference matrix file
    verify_files([verify_cond,
                  op.join(output_dir, 'test_diff_file.json'),
                  "-e",
                  exclude_items,
                  "-r",
                  reference_cond
                  ])
    log_info("JSON difference file is created!")

    # (3) Get processes that create differences
    spot([sqlite_db,
          op.join(output_dir, 'test_diff_file.json'),
          "-o", spot_classify_file,
          "-i",
          exclude_items,
          "-c"
          ])
    log_info("Processes are classified in JSON file!")


def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or \
               os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def capture(descriptor, invocation, output_dir,
            commands, wrapper_script, ref_cond, process_list):
    tag_name = '000'
    image_name = json_file_editor(descriptor)
    make_modify_script(output_dir, commands, wrapper_script)
    modify_docker_image(descriptor, output_dir, tag_name, ref_cond,
                        ref_cond, process_list)
    log_info("Docker is modified on the First condition "
             "to capture all the temporary and multi-write files")
    # (2-1) Execute pipeline to persist the temporary
    # and mnulti-write processes
    pipeline_executor(descriptor, invocation)  # CENTOS6
    log_info("all the files are captured")
    # restart to the default parameters and clean backup directory
    json_file_editor(descriptor, image_name, 'image')
    backup_path = op.join(output_dir, 'backup_scripts')
    # for f in os.listdir(backup_path):
    shutil.rmtree(backup_path)

    # move temp captured files from backup directory into the original path
    src = op.join(ref_cond, "spot_temp")
    copytree(src, ref_cond, symlinks=False, ignore=None)
#    sys.exit(1)


def modify(descriptor, invocation, output_dir,
           sqlite_db, wrapper_script, from_path, to_path, process_list):
    tag_name = '999'
    log_info("Pipeline executed, "
             "going to find new process that create error!")
    lst_proc = get_processes_list(sqlite_db)
    image_name = json_file_editor(descriptor)

    make_modify_script(output_dir, lst_proc, wrapper_script)
    modify_docker_image(descriptor, output_dir, tag_name, from_path,
                        to_path, process_list)
    log_info("Docker is modified on the Reference condition"
             "to fix process that create errors ")
    # (3-1) Execute pipeline to capture all the processes with differences
    pipeline_executor(descriptor, invocation)  # CENTOS7
    log_info("Pipeline executed!!")

    json_file_editor(descriptor, image_name, 'image')
    backup_path = op.join(output_dir, 'backup_scripts')
    shutil.rmtree(backup_path)


def write_arguments(subj_name, verify_condition, exclude_items, sqlite_db,
                    captured_list, process_list):
    info = {}
    info_ = {}
    info_["subject_name"] = subj_name
    info_["conditions"] = verify_condition
    info_["exclude_items"] = exclude_items
    info_["sqlite_db"] = sqlite_db
    info_["captured_list"] = captured_list
    info["execution_info"] = info_
    info['ignored_multi'] = []
    with open(process_list, 'w+') as write_info:
        json.dump(info, write_info, indent=4, sort_keys=True)


def main(args=None):
    parser = argparse.ArgumentParser(description='Automation of pipeline '
                                                 ' error detection')
    parser.add_argument("output_directory", help='directory where to '
                                                 'store the outputs')
    parser.add_argument("-c", "--verify_condition",
                        help="input the text file containing the path "
                             "to the verify_file condition folders")
    parser.add_argument("-e", "--exclude_items",
                        help="The list of items to be ignored while "
                             "parsing the files and directories")
    parser.add_argument("-s", "--sqlite_db",
                        help="sqlite file created by reprozip")
    parser.add_argument("-m", "--wrapper_script",
                        help="the python script that should be replaced "
                             "by the original pipeline execution files")
    parser.add_argument("-o", "--spot_output",
                        help=".json output file of spot")
    #  parser.add_argument("-r", "--reference_cond", action='store_true',
    #                      help="Insert path of reference condition to "
    #                            "capture temp and multi-write files")
    parser.add_argument("-d", "--base_descriptor",
                        help="Boutiques descriptor")
    parser.add_argument("-i", "--base_invocation",
                        help="Boutiques invocation")
    parser.add_argument("-d2", "--ref_descriptor",
                        help="Boutiques descriptor of the reference condition")
    parser.add_argument("-i2", "--ref_invocation",
                        help="Boutiques invocation of the reference condition")
    parser.add_argument("-r", "--reference_cond",
                        help="path directory to the output files of reference "
                             "condition to capture temp and multi-write files."
                             "Also, it make copies FROM this directory.")
    parser.add_argument("-b", "--base_cond",
                        help="path directory to the output files of base "
                             "condition that make copies TO this directory.")

    logging.basicConfig(format='%(asctime)s:%(message)s',
                        level=logging.INFO)
    args = parser.parse_args(args)

    spot_classify_file = op.join(op.abspath(args.output_directory),
                                 args.spot_output)
    # (1) First pipeline execution in Condition 1
    # (reference condition-CENTOS6) to produce
    # process tree and result files
    # pipeline_executor(args.ref_descriptor, args.ref_invocation)
    log_info("pipelines executed on Condition 1")

    classify_process(op.abspath(args.verify_condition),
                     op.abspath(args.exclude_items),
                     op.abspath(args.output_directory),
                     op.abspath(args.sqlite_db),
                     spot_classify_file,
                     op.abspath(args.reference_cond))
    spot_capture_file = (os.path.splitext(spot_classify_file)[0] +
                         '_captured.json')
    commands = {}
    wrapper_script = op.basename(args.wrapper_script)
    shutil.copyfile(args.wrapper_script, op.join(args.output_directory,
                                                 wrapper_script))
    with open(spot_capture_file, 'r') as tmp_cmd:
        data = json.load(tmp_cmd)

    subj_name = data["execution_info"]["subject_name"]
    # write arguments on json file to read from wrapper file
    write_arguments(subj_name, op.abspath(args.verify_condition),
                    op.abspath(args.exclude_items),
                    op.abspath(args.sqlite_db),
                    spot_capture_file,
                    spot_classify_file)

    reference_cond = op.join(op.abspath(args.reference_cond), subj_name)
    base_cond = op.join(op.abspath(args.base_cond), subj_name)

    commands.update(data["total_temp_proc"])
    commands.update(data["total_multi_write_proc"])
    # if args.capture_mode:
    if commands:
        # (2) Second pipeline execution in Condition 1
        # to capture multi-write and temporary files
        capture(args.ref_descriptor,
                args.ref_invocation,
                op.abspath(args.output_directory),
                commands,
                op.abspath(wrapper_script),
                reference_cond, spot_classify_file)

        log_info("temp and multi-write processes are captured on "
                 "base conditions!")
        os.rename(spot_capture_file,
                  spot_capture_file.replace('.json', '_c.json'))

    # (3) Third pipeline execution in Condition 2
    # (based condition - CENTOS7) to label process graph
    modify(args.base_descriptor,
           args.base_invocation,
           op.abspath(args.output_directory),
           op.abspath(args.sqlite_db),
           op.abspath(wrapper_script),
           reference_cond,
           base_cond, spot_classify_file)
    log_info("All the pipeline rocesses are classified through modifications!")


if __name__ == '__main__':
    main()
