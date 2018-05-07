#!/bin/bash

'''
Pre-processing: after preparing the result of first condition (CentOS6)
and getting the processes tree of pipeline using reprozip (db_sqlite), 
we will detect the pipeline errors and the modify them in the following steps:
(1) Running pipeline on the other condition (Centos7) to get the results
(2) Running verify_files.py with results of two conditions to get the matrix file
(3) Running 'peds.py' script based on the matrix file and db_sqlite 
    to get a command_line list include all the claddified process
(4) Modification step to fix the detected processes with error artificially
(5) if command_line list is empty: break; else go step (1)
'''

# Start Modification Loop
while [ -s /home/ubuntu/PEDS/test/peds_test/command_lines.txt ]
do

#(1) Start the Pipeline execution
cd /home/ubuntu/PEDS/test/peds_test/centos7/test
sh test_script.sh input_file.txt
cd ../..

#(2) Start to create the error matrix file
python ../../verifyFiles.py conditions.txt test result
awk '{print $1,$2}' result/test_differences_subject_total.txt > error_matrix.txt
tail -n +2 error_matrix.txt > temp.tmp && mv temp.tmp error_matrix.txt

#(3) Start the classification
python ../../bin/peds.py -db trace.sqlite3 -ofile error_matrix.txt

if [ -s command_lines.txt ]
then
    cat command_lines.txt >> updated_commands.txt
else
    echo "command_line is empty, last iteration"
fi

#(4) Start the modification
python ../../bin/modif_script.py updated_commands.txt

done
