#!/usr/bin/python

import argparse
import subprocess
import sys
import fileinput
import csv
import re
import os
import os.path as op
from shutil import copyfile
import logging
import json
import boutiques
import docker
from reprotools import __file__ as repro_path
from reprotools.verify_files import main as verify_files
from reprotools.peds import main as peds


# Pre-processing: after preparing the result of first condition (CentOS6)
# and getting the processes tree of pipeline using reprozip (db_sqlite),
# we detect the pipeline errors then modify them in the following steps:
# (1) Running pipeline on the other condition (Centos7) to get the results
# (2) Running verify_files.py with results of two conditions to get the
# matrix file
# (3) Running 'peds.py' script based on the matrix file and db_sqlite
#    to get a command_line list include all the classified process
# (4) Modification step to fix the detected processes with error artificially
# (5) if command_line list is empty: break; else go step (1)"


def log_info(message):
    logging.info("INFO: " + message)


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


def pipeline_executor(descriptor, invocation):
    with open(descriptor, 'r') as jsonFile:
        data = json.load(jsonFile)
    # Check that Boutiques descriptor has a Docker container
    if data["container-image"]["type"] != 'docker':
        sys.exit("Container must be a docker image!")
    print("Docker image: {}".format(data["container-image"]["image"]))

    try:
        print("Launching Boutiques tool")
        output_object = boutiques.execute("launch", descriptor, invocation)
    except SystemExit as e:
        return(e.code)
    print(output_object)
    if(output_object.exit_code):
        sys.exit("Pipeline execution failed.")


def make_modify_script(peds_data_path, command_dic):
    cmd_file = open(op.join(peds_data_path, 'cmd.sh'), 'w+')
    cmd_file.write('#!/usr/bin/env bash \n')
    cmd_list = []
    for command, files in command_dic.items():
        pipeline_command = command.split('\x00')[0]
        if pipeline_command not in cmd_list:
            cmd_list.append(pipeline_command)
            # Make a copy of process to backup folder if doesn't exist
            if pipeline_command.split('/')[0] == '':
                pipeline_command_new = pipeline_command[1:]
                backup_path = op.join(peds_data_path,
                                      'backup_scripts', pipeline_command_new)
            else:
                backup_path = op.join(peds_data_path,
                                      'backup_scripts', pipeline_command)

            if not op.exists(backup_path):
                if not op.exists(op.dirname(backup_path)):
                    os.makedirs(op.dirname(backup_path))
                cmd_file.write('cp ' + '`which '+pipeline_command + '` '
                               + backup_path + '\n')
                cwd = op.abspath(op.join(os.getcwd(), '../..'))
                cmd_file.write('cp ' + op.join(cwd,
                               'make_copy.py') + ' `which ' +
                               pipeline_command + '`' + '\n')
                # ~ cmd_file.write('cp ' + op.join(op.dirname(__file__),
                #               # ~ 'make_copy.py') + ' `which ' +
                #               # ~ pipeline_command + '`' + '\n')


def modify_docker_image(descriptor, peds_data_path, tag_name):
    with open(descriptor, 'r') as jsonFile:
        data = json.load(jsonFile)
    image_name = data["container-image"]["image"]
    client = docker.from_env()
    # print("Running command: {}".format(cmd_list))
    cwd = op.abspath(op.join(os.getcwd(), '../..'))

    print(cwd)
    cmd_file_path = op.join(peds_data_path, 'cmd.sh')
    with open(cmd_file_path, 'r') as cmdFile:
        cmd = cmdFile.readlines()
    container = client.containers.run(image_name,
                                      command='sh ' + cmd_file_path,
                                      volumes={cwd:
                                               {'bind': cwd,
                                                'mode': 'rw'}},
                                      environment=(["PYTHONPATH=$PYTHONPATH:"
                                                   + cwd,
                                                   "REPRO_TOOLS_PATH=" +
                                                    os.getcwd()]),
                                      working_dir=cwd,
                                      detach=True)
    container.logs()
    container.wait()
    new_img_name = image_name.split(':')[0] + "_" + str(tag_name)
    image = container.commit(new_img_name)
    json_file_editor(descriptor, new_img_name, 'image')
    # ~ data["container-image"]["image"] = new_img_name
    # ~ with open(descriptor, 'w+') as jsonFile:
    # ~ json.dump(data, jsonFile)


def json_file_editor(descriptor, new_param, act):
    with open(descriptor, 'r') as jsonFileR:
        data = json.load(jsonFileR)
    if act == "image":
        data["container-image"]["image"] = new_param
    elif act == "None":
        # ~ data["total_multi_write_proc"] = {}
        # ~ data["total_temp_proc"] = {}
        data = {}
    with open(descriptor, 'w+') as jsonFileW:
        json.dump(data, jsonFileW, indent=4, sort_keys=True)


def update_peds_json(total_commands, output_peds_file, cond):
    with open(output_peds_file, 'r') as rfile:
        data = json.load(rfile)
    if cond is "single":
        data["total_commands"] = total_commands
    elif cond is "multi":
        data["total_commands_multi"] = total_commands
    with open(output_peds_file, 'w+') as ufile:
        json.dump(data, ufile, indent=4, sort_keys=True)


def capture(descriptor,
            invocation,
            descriptor_cond2,
            invocation_cond2,
            verify_cond,
            verify_output,
            peds_data_path,
            sqlite_db,
            peds_result,
            peds_capture_output,
            condition,
            output_peds_file):
    # (1) Start the Pipeline execution using bosh
    pipeline_executor(descriptor, invocation)  # CENTOS7
    pipeline_executor(descriptor_cond2, invocation_cond2)  # CENTOS6
    log_info("pipelines executed on both conditions!")

    # (2) Get the error matrix file
    verify_files([verify_cond,
                  op.join(verify_output, 'test_diff_file.json'),
                  "-e",
                  op.join(peds_data_path, 'exclude_items.txt')
                  ])

    # (3) Get total multi_write and temp commands
    peds([sqlite_db,
          "test_diff_file.json",
          "-o", peds_result,
          "-c"
          ])

    # (4) Capturing multi-write process in the ref condition (centos6)
    # and all Temporary files in both conditions (Just One time)
    tag_name = 0
    tag_name_cond2 = 0
    with open(peds_capture_output, 'r') as tmp_cmd:
        data = json.load(tmp_cmd)
    if data["total_temp_proc"]:
        tag_name += 1
        tag_name_cond2 += 1
        make_modify_script(peds_data_path, data["total_temp_proc"])

        if condition == 'first':
            modify_docker_image(descriptor, peds_data_path, tag_name)
            log_info("Docker is modified on the First condition "
                     "to capture all the temporaty files")
        else:
            modify_docker_image(descriptor_cond2, peds_data_path,
                                tag_name_cond2)
            log_info("Docker is modified on the Second condition "
                     "to capture all the temporaty files")

    if data["total_multi_write_proc"]:
        tag_name += 1
        tag_name_cond2 += 1
        make_modify_script(peds_data_path, data["total_multi_write_proc"])
        if condition == 'first':
            modify_docker_image(descriptor, peds_data_path, tag_name)
            log_info("Docker is modified on the First condition "
                     "to capture all the files with multi-writes")
        else:
            modify_docker_image(descriptor_cond2, peds_data_path,
                                tag_name_cond2)
            log_info("Docker is modified on the Second condition "
                     "to capture all the files with multi-writes")

    # (4-1) Execute ref condition pipeline to persist the temporary
    # and mnulti-write process in the second condition
    json_file_editor(output_peds_file, '', 'None')
    if condition == 'first':
        pipeline_executor(descriptor, invocation)  # CENTOS7
        log_info("all the files are captured on the First condition")
    else:
        pipeline_executor(descriptor_cond2, invocation_cond2)  # CENTOS6
        log_info("all the files are captured on the Second condition")

    backup_path = op.join(peds_data_path, 'backup_scripts')
    for f in os.listdir(backup_path):
        os.remove(os.path.join(backup_path, f))
    json_file_editor(descriptor, 'peds_centos7', 'image')
    json_file_editor(descriptor_cond2, 'peds_centos6', 'image')


def iterate(descriptor,
            invocation,
            descriptor_cond2,
            invocation_cond2,
            verify_cond,
            verify_output,
            peds_data_path,
            sqlite_db,
            peds_result,
            peds_capture_output,
            output_peds_file):
    # Start Modification Loop
    tag_name = 0
    total_commands = {}
    total_mutli_write = {}
    pipeline_executor(descriptor_cond2, invocation_cond2)
    while True:
        # (1) Start the Pipeline execution using bosh
        pipeline_executor(descriptor, invocation)
        log_info("Pipeline executed, "
                 "going to find new process that create error!")

        # (2) Running VerifyFiles script to make error matrix file
        verify_files([verify_cond,
                      op.join(verify_output, 'test_diff_file.json'),
                      "-e",
                      op.join(verify_output, 'exclude_items.txt')
                      ])

        # (3) Classification of processes, running peds script
        print([sqlite_db,
               "test_diff_file.json",
               "-o", peds_result
               ])
        peds([sqlite_db,
              "test_diff_file.json",
              "-o", peds_result
              ])
        json_file_editor(peds_capture_output, '', 'None')
        log_info("peds has done!")

        # Check if there exist processes that create error
        with open(output_peds_file, 'r') as cmd_json:
            data = json.load(cmd_json)
        if data["multiWrite_cmd"]:
            print("MULTI:  ")
            total_mutli_write.update(data["multiWrite_cmd"])
            update_peds_json(total_mutli_write, output_peds_file, "multi")
            tag_name += 1
            make_modify_script(peds_data_path, data["multiWrite_cmd"])
            modify_docker_image(descriptor, peds_data_path, tag_name)
            log_info("Docker is modified on the Reference condition"
                     "to fix process with multiple-writes, "
                     "going to the next iteration")

        if data["certain_cmd"]:
            print("Certain:  ")
            # (4) Start the modification through docker image
            total_commands.update(data["certain_cmd"])
            update_peds_json(total_commands, output_peds_file, "single")
            # make a bash script include the commands of
            # modifications to run inside the docker image
            tag_name += 1
            make_modify_script(peds_data_path, data["certain_cmd"])
            # commit the container with a new image name, e.g., peds_1234
            # and modify the Boutiques descriptor to use the new image
            modify_docker_image(descriptor, peds_data_path, tag_name)
            log_info("Docker is modified on the Reference condition"
                     "to fix process that create errors with certain cmd, "
                     "goint to the next iteration")
            # ~ sys.exit(1)
        if not (data["certain_cmd"] or data["multiWrite_cmd"]):
            log_info("there are no error in the pipeline!")
            # print out the final recognized processes
            update_peds_json(total_mutli_write, output_peds_file, "multi")
            update_peds_json(total_commands, output_peds_file, "single")

            backup_path = op.join(peds_data_path, 'backup_scripts')
            for f in os.listdir(backup_path):
                os.remove(os.path.join(backup_path, f))
            json_file_editor(descriptor, 'peds_centos7', 'image')
            json_file_editor(descriptor_cond2, 'peds_centos6', 'image')

            break


def main(args=None):
    parser = argparse.ArgumentParser(description='Automation of pipeline '
                                                 ' error detection')
    parser.add_argument("output_directory", help='directory where to '
                                                 'store the output')
    parser.add_argument("-c", "--verify_condition",
                        help="input the text file containing the path "
                             "to the verify_file condition folders")
    parser.add_argument("-r", "--verify_output",
                        help="path of verify_file outputs")
    parser.add_argument("-s", "--sqlite_db",
                        help="sqlite file created by reprozip")
    parser.add_argument("-o", "--peds_output",
                        help=".json output file of peds")
    parser.add_argument("-m", "--capture_mode", action='store_true',
                        help="include two values (True and False) to indicate"
                              "capturing temp and multi-write files (true)"
                              " or making modification steps (false)")
    parser.add_argument("-p", "--cap_condition",
                        help="which condition to capture files")
    parser.add_argument("-d", "--descriptor",
                        help="Boutiques descriptor")
    parser.add_argument("-i", "--invocation",
                        help="Boutiques invocation")
    parser.add_argument("-d2", "--descriptor_cond2",
                        help="Boutiques descriptor for the second condition")
    parser.add_argument("-i2", "--invocation_cond2",
                        help="Boutiques invocation for the second condition")

    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
    args = parser.parse_args(args)

    output_peds_file = op.join(op.abspath(args.output_directory),
                               args.peds_output)
    peds_capture_output = (os.path.splitext(output_peds_file)[0] +
                           '_captured.json')
    condition = args.cap_condition

# Start to persist temporary and multi version files in both conditions
    if args.capture_mode:
        capture(args.descriptor,
                args.invocation,
                args.descriptor_cond2,
                args.invocation_cond2,
                args.verify_condition,
                args.verify_output,
                op.abspath(args.output_directory),
                op.abspath(args.sqlite_db),
                args.peds_output,
                peds_capture_output,
                condition,
                output_peds_file)
    else:
        iterate(args.descriptor,
                args.invocation,
                args.descriptor_cond2,
                args.invocation_cond2,
                args.verify_condition,
                args.verify_output,
                op.abspath(args.output_directory),
                op.abspath(args.sqlite_db),
                args.peds_output,
                peds_capture_output,
                output_peds_file
                )


if __name__ == '__main__':
    main()
