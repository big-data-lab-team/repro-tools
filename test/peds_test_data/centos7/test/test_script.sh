#!/usr/bin/env bash

if [ $# != 1 ]
then
    echo "usage: $0 <input_file.txt> <output_folder>"
    exit 1
fi

input_file=$1
centos7=7
#unamestr=`cat /etc/*-release | grep -o "'[0-9]\.[0-9]'"`
unamestr=7
#shopt -s xpg_echo

if [ ${unamestr} -eq ${centos7} ]
then    
    grep line ${input_file} > f1.out
else
    
    grep centos ${input_file} > f1.out
fi

grep line3 f1.out > f2.out

if [ ${unamestr} -eq ${centos7} ]
then
    grep centos7 f1.out > f3.out
else
    grep line f1.out > f3.out
fi

grep line f3.out > f4.out
