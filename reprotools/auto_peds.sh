#!/bin/bash

set -e
set -u

#Pre-processing: after preparing the result of first condition (CentOS6)
#and getting the processes tree of pipeline using reprozip (db_sqlite), 
#we will detect the pipeline errors and the modify them in the following steps:
#(1) Running pipeline on the other condition (Centos7) to get the results
#(2) Running verify_files.py with results of two conditions to get the matrix file
#(3) Running 'peds.py' script based on the matrix file and db_sqlite 
#    to get a command_line list include all the claddified process
#(4) Modification step to fix the detected processes with error artificially
#(5) if command_line list is empty: break; else go step (1)

pipeline_script=$1
input_file=$2
command_lines_file="command_lines.txt"
echo initialization > ${command_lines_file}
# Start Modification Loop
while [ -s ${command_lines_file} ]
do
#(1) Start the Pipeline execution
${pipeline_script} ${input_file}

#(2) Start to create the error matrix file
verifyFiles test/peds_test/conditions.txt test result
awk '{print $1,$2}' ./result/test_differences_subject_total.txt | tail -n +2 > error_matrix.txt

#(3) Start the classification
peds -db test/peds_test/trace.sqlite3 -ofile error_matrix.txt

if [ -s ${command_lines_file} ]
then
    cat ${command_lines_file} >> updated_commands.txt
else
    echo "command_line is empty, last iteration"
fi

#(4) Start the modification
modif_script updated_commands.txt

done
echo "Done!"
