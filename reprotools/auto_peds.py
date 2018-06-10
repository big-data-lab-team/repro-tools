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


def make_modify_script(peds_data_path, command_dic):
    for command, files in command_dic.items():
        pipeline_command = command.split('\x00')[0]
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


def update_peds_json(total_commands, output_peds_file):
	with open(output_peds_file, 'r') as rfile:
		data = json.load(rfile)
	data["total_commands"] = total_commands
	with open(output_peds_file, 'w') as ufile:
		json.dump(data, ufile)


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
    parser.add_argument("-d", "--descriptor",
                        help="Boutiques descriptor")
    parser.add_argument("-i", "--invocation",
                        help="Boutiques invocation")
    args = parser.parse_args()
    descriptor = args.descriptor
    invocation = args.invocation
    peds_result = args.peds_output
    peds_data_path = op.abspath(args.output_directory)
    verify_cond = args.verify_condition
    verify_output = args.verify_output
    sqlite_db = op.abspath(args.sqlite_db)
    first_iter = True
    tag_name = 0
    total_commands={}
# Start Modification Loop
    while True:       

        # (1) Start the Pipeline execution using bosh
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

        # (2) Running VerifyFiles script to make error matrix file
        verify_command = 'verify_files ' + verify_cond + ' test ' + verify_output
        bash_executor(os.getcwd(), verify_command)

        # (3) Classification of processes, running peds script
        peds_command = "peds " + sqlite_db + " " + " test_differences_subject_total.txt" + " -o " + peds_result
        bash_executor(peds_data_path, peds_command)
        
        # Check if there exist processes that create error
        output_peds_file = op.join(peds_data_path, peds_result)
        with open(output_peds_file, 'r') as cmd_json:
            data = json.load(cmd_json)
        if data["certain_cmd"]:
        # (4) Start the modification through docker image
            total_commands.update(data["certain_cmd"])
            update_peds_json(total_commands, output_peds_file)
            tag_name += 1
            # make a bash script include the commands of 
            # modifications to run inside the docker image
            make_modify_script(peds_data_path, data["certain_cmd"])
            # commit the container with a new image name, e.g., peds_1234
            # and modify the Boutiques descriptor to use the new image
            modify_docker_image(descriptor, peds_data_path, tag_name)
        else:
			# print out the final recognized processes
            update_peds_json(total_commands, output_peds_file)
            break


if __name__ == '__main__':
    main()
