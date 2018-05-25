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
import json
import boutiques
import docker

# Pre-processing: after preparing the result of first condition (CentOS6)
# and getting the processes tree of pipeline using reprozip (db_sqlite),
# we detect the pipeline errors and the modify them in the following steps:
# (1) Running pipeline on the other condition (Centos7) to get the results
# (2) Running verify_files.py with results of two conditions to get the
# matrix file
# (3) Running 'peds.py' script based on the matrix file and db_sqlite
#    to get a command_line list include all the claddified process
# (4) Modification step to fix the detected processes with error artificially
# (5) if command_line list is empty: break; else go step (1)"


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


def bash_executor(execution_dir, command):
    process = subprocess.Popen(command,
                               shell=True,
                               stderr=subprocess.PIPE,
                               cwd=execution_dir)
    output, error = process.communicate()
    if(process.returncode):
        if output:
            print(output)
        if error:
            print(error)
        raise Exception("Command execution failed")


def make_modify_script(peds_data_path):
    with open(op.join(peds_data_path, 'command_lines.txt'), 'r') as cfile:
        lines = cfile.readlines()
        for line in lines:
            commands = str(line).split('##')[:1]
            pipeline_command = commands[0].replace('\x00', ' ').split(' ')[0]
            # Make a copy of process to backup folder if doesn't exist
            backup_path = op.join(peds_data_path,
                                       'backup_scripts',
                                       pipeline_command)
            cmd_file = open(op.join(peds_data_path, 'cmd.sh'), 'w+')
            cmd_file.write('#!/usr/bin/env bash \n')

            if not op.exists(backup_path):
                if not op.exists(op.dirname(backup_path)):
                    os.makedirs(op.dirname(backup_path))
                cmd_file.write('cp ' + '`which '+pipeline_command + '` '
                                + backup_path + '\n')
                cmd_file.write('cp ' + op.join(op.dirname(__file__),
                                                'make_copy.py') +
                                ' `which '+pipeline_command + '`' + '\n')


def modify_docker_image(descriptor, peds_data_path, tag_name):
    # image_name = "salari/peds:centos7-test2"
    with open(descriptor, 'r') as jsonFile:
        data = json.load(jsonFile)
    image_name = data["container-image"]["image"]
    client = docker.from_env()
    # print("Running command: {}".format(cmd_list))

    cmd_file_path = op.join(peds_data_path, 'cmd.sh')
    with open(cmd_file_path, 'r') as cmdFile:
        cmd = cmdFile.readlines()
    container = client.containers.run(image_name,
                                      command='sh ' + cmd_file_path,
                                      volumes={os.getcwd():
                                               {'bind': os.getcwd(),
                                                'mode': 'rw'}},
                                      environment=["PYTHONPATH=$PYTHONPATH:"+os.getcwd()],
                                      working_dir=os.getcwd(),
                                      detach=True)
    container.logs()
    container.wait()
    new_img_name = image_name.split(':')[0] + "_" + str(tag_name)  #tag=12345
    image = container.commit(new_img_name)

    data["container-image"]["image"] = new_img_name
    with open(descriptor, 'w+') as jsonFile:
        json.dump(data, jsonFile)


def main(args=None):
    # Use argparse
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
    parser.add_argument("-d", "--descriptor",
                        help="Boutiques descriptor")
    parser.add_argument("-i", "--invocation",
                        help="Boutiques invocation")
    args = parser.parse_args()
    descriptor = args.descriptor
    invocation = args.invocation
    peds_data_path = op.abspath(args.output_directory)
    verify_cond = args.verify_condition
    verify_output = args.verify_output
    sqlite_db = op.abspath(args.sqlite_db)
    first_iter = True
    tag_name = 0
# Start Modification Loop
    while True:       
        # (1) Start the Pipeline execution
        # pipeline_command = pipe_exec+" "+pipe_input
        # bash_executor(pipe_output, pipeline_command)
        # (A) get a Boutiques descriptor and invocation.
        # Check that Boutiques descriptor has a Docker container (not
        # Singularity, not no container)
        with open(descriptor, 'r') as jsonFile:
            data = json.load(jsonFile)
        if data["container-image"]["type"] != 'docker':
            sys.exit("Container must be a docker image!")
        print("Docker image: {}".format(data["container-image"]["image"]))

        # set invocation parameters entered by user
        # (B) run the pipeline using bosh.
        #      from boutiques import bosh
        #      output_object = bosh.execute("launch", descriptor, invocation)
        #      check that execution succeeded in output_object
        try:
            print("Launching Boutiques tool")
            output_object = boutiques.execute("launch", descriptor, invocation)
        except SystemExit as e:
            return(e.code)
        print(output_object)
        if(output_object.exit_code):
            sys.exit("Pipeline execution failed.")

        #  (C) do your analysis, modify the Docker container in the Boutiques descriptor:
        #        1. run a container and modify it
        #        2. commit the container with a new image name, e.g., <init_name>_peds_1234. Use the Docker Python API for it: https://docker-py.readthedocs.io/en/stable/containers.html
        #        3. Modify the Boutiques descriptor to use the new image
        #  (D) GOTO (B)

        # (2) Create error matrix file
        verify_command = 'verify_files ' + verify_cond + ' test ' + verify_output
        bash_executor(os.getcwd(), verify_command)

        with open(op.join(verify_output, 'test_differences_subject_total.txt'), 'r') as mfile:
            lines = mfile.readlines()
        sample = ""
        for line in lines[1:]:
            splited_line = line.split('\t')
            sample += (splited_line[0].replace(' ', '') + " " + str(int(splited_line[1]))+os.linesep)
        write_matrix = open(op.join(peds_data_path, 'error_matrix.txt'), 'w')
        write_matrix.write(sample)
        write_matrix.close()

        # (3) Classification of processes
        #if first_iter is True:
        #    os.remove(os.path.join(peds_data_path, 'total_commands.txt'))
        #    first_iter = False
        peds_command = "peds -d " + sqlite_db + " -m error_matrix.txt"
        bash_executor(peds_data_path, peds_command)

        # (4) Start the modification
        if os.stat(op.join(peds_data_path, 'command_lines.txt')).st_size > 0:
            tag_name += 1
            make_modify_script(peds_data_path)
            modify_docker_image(descriptor, peds_data_path, tag_name)
        else:
            break


if __name__ == '__main__':
    main()
