#!/usr/bin/python

import argparse
import subprocess
import sys
import fileinput
import csv
import re
import os.path
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
        (path, name) = os.path.split(exe)
        if os.access(exe, os.X_OK):
            return exe
        for path in os.environ.get('PATH').split(os.pathsep):
            full_path = os.path.join(path, exe)
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
        raise Exception("Pipeline execution failed")


def replace_script(peds_data_path):
    with open(os.path.join(peds_data_path, 'command_lines.txt'), 'r') as cfile:
        lines = cfile.readlines()
        for line in lines:
            command_list = []
            commands = str(line).split('##')[:1]
            pipeline_command = commands[0].replace('\x00', ' ').split(' ')[0]
            # Make a copy of process to backup folder if doesn't exist
            backup_path = os.path.join(peds_data_path, 'backup_scripts', pipeline_command)
            if not os.path.exists(backup_path):
                if not os.path.exists(os.path.dirname(backup_path)):
                    os.makedirs(os.path.dirname(backup_path))
                command_list.append('cp '+which(pipeline_command)+' '+ backup_path)
                command_list.append('cp '+os.path.join(os.path.dirname(__file__), 'make_copy.py')+' '+ which(pipeline_command))
#                copyfile(which(pipeline_command), backup_path)
#                copyfile(os.path.join(os.path.dirname(__file__), 'make_copy.py'), which(pipeline_command))
    return command_list


def modify_docker_image(descriptor, cmd_list):
#image_name = "salari/peds:centos7-test2"
    with open (descriptor, 'r') as jsonFile:
        data = json.load(jsonFile)
    image_name = data["container-image"]["image"]

    client = docker.from_env()
    container = client.containers.run(image_name, 
                                      command=cmd_list, 
                                      volumes={os.getcwd(): {'bind': os.getcwd(), 'mode': 'rw'}}, 
                                      detach=True)
    #ctr = c.containers.run(image_name, command="bash -c ' for((i=1;i<=10;i+=2)); do echo Welcome $i times; sleep 10; done'", detach=True) 
    container.wait()
    new_img_name = image_name.split(':')[0]+"_"+"3" #"new_tag=12345"
    image = container.commit(new_img_name)
    print image.id

    data["container-image"]["image"] = new_img_name   
    with open (descriptor, 'w+') as jsonFile:
        json.dump(data, jsonFile)


def main(args=None):
    # Use argparse
    parser = argparse.ArgumentParser(description='Automation of pipeline error detection')
    parser.add_argument("output_directory", help="directory where to store the output")
    parser.add_argument("-p", "--pipe_exec",
                        help="executions file of the pipeline")
    parser.add_argument("-i", "--pipe_input",
                        help="input data of pipeline running")
    parser.add_argument("-o", "--pipe_output",
                        help="path of pipeline output directory")
    parser.add_argument("-c", "--verify_condition",
                        help="input the text file containing the path to the verify_file condition folders")
    parser.add_argument("-r", "--verify_output",
                        help="path of verify_file outputs")
    parser.add_argument("-s", "--sqlite_db",
                        help="sqlite file created by reprozip")
    parser.add_argument("-d", "--descriptor",
                        help="Boutiques descriptor")
    parser.add_argument("-in", "--invocation",
                        help="Boutiques invocation")
    args = parser.parse_args()
    descriptor = args.descriptor
    invocation = args.invocation
    peds_data_path = os.path.abspath(args.output_directory)
    pipe_exec = os.path.abspath(args.pipe_exec)
    pipe_input = os.path.abspath(args.pipe_input)
    pipe_output = os.path.abspath(args.pipe_output)
    verify_cond = args.verify_condition
    verify_output = args.verify_output
    sqlite_db = os.path.abspath(args.sqlite_db)
    first_iter = True
# Start Modification Loop
    while True:

        # (1) Start the Pipeline execution
        # pipeline_command = pipe_exec+" "+pipe_input
        # bash_executor(pipe_output, pipeline_command)
        # (A) get a Boutiques descriptor and invocation. Check that Boutiques descriptor has a Docker container (not Singularity, not no container)
        with open (descriptor, 'r') as jsonFile:
            data = json.load(jsonFile)
        if data["container-image"]["type"] != 'docker':
            sys.exit("Container should be a docker image!")

# set invocation parameters entered by user
        with open (invocation, 'r') as invocJson:
            invoc_data = json.load(invocJson)
        invoc_data["input_file"] = pipe_input
        invoc_data["output_file"] = pipe_output
        with open (invocation, 'w+') as invocJson:
            json.dump(invoc_data, invocJson)
        # (B) run the pipeline using bosh. 
        #      from boutiques import bosh
        #      output_object = bosh.execute("launch", descriptor, invocation)
        #      check that execution succeeded in output_object
        try:
            output_object = boutiques.execute("launch", descriptor, invocation)
        except SystemExit as e:
            return(e.code)

        #  (C) do your analysis, modify the Docker container in the Boutiques descriptor:
        #        1. run a container and modify it
        #        2. commit the container with a new image name, e.g., <init_name>_peds_1234. Use the Docker Python API for it: https://docker-py.readthedocs.io/en/stable/containers.html
        #        3. Modify the Boutiques descriptor to use the new image
        #  (D) GOTO (B)


        # (2) Start to create the error matrix file
        verify_command = 'verify_files ' + verify_cond + ' test ' + verify_output
        bash_executor(os.getcwd(), verify_command)

        with open(os.path.join(verify_output, 'test_differences_subject_total.txt'), 'r') as mfile:
            lines = mfile.readlines()
        sample = ""
        for line in lines[1:]:
            splitedLine = line.split('\t')
            sample += (splitedLine[0].replace(' ', '') + " " + str(int(splitedLine[1]))+"\n")
        write_matrix = open(os.path.join(peds_data_path, 'error_matrix.txt'), 'w')
        write_matrix.write(sample)
        write_matrix.close()

        # (3) Start the classification
#        if first_iter is True:
#            os.remove(os.path.join(peds_data_path, 'total_commands.txt'))
#            first_iter = False
        peds_command = "peds -d " + sqlite_db + " -m error_matrix.txt"
        bash_executor(peds_data_path, peds_command)

        # (4) Start the modification
        if os.stat(os.path.join(peds_data_path, 'command_lines.txt')).st_size > 0:
            cmd_list = replace_script(peds_data_path)
            modify_docker_image(descriptor, cmd_list)

        else: break


if __name__ == '__main__':
    main()
