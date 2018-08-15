#!/usr/bin/env bash

if [ $# != 2 ]
then
    echo "usage: $0 <input_file.txt> <output_folder>"
    exit 1
fi

input_file=$1
out=$2
centos7=6
#unamestr=`cat /etc/*-release | grep -o "'[0-9]\.[0-9]'"`
unamestr=7
#shopt -s xpg_echo

if [ ${unamestr} -eq ${centos7} ]
then    
    grep line ${input_file} > ${out}/f1.out
else
    
    grep centos ${input_file} > ${out}/f1.out
fi

grep line3 ${out}/f1.out > ${out}/f2.out

if [ ${unamestr} -eq ${centos7} ]
then
    grep centos7 ${out}/f1.out > ${out}/f3.out
else
    grep line ${out}/f1.out > ${out}/f3.out
fi

grep line ${out}/f3.out > ${out}/f4.out
