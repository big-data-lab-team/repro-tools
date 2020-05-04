#!/usr/bin/env bash

if [ $# != 2 ]
then
echo "usage: $0 <input_file.txt> <output_folder>"
exit 1
fi

input_file=$1
out=$2
unamestr="$(cat /etc/*-release | grep -o '[0-9]\.[0-9]' | head -n 1)" #=> 7.5 ^ 6.1

grep ${unamestr} ${input_file} > ${out}/f1.out   # '1#grep' Single error

grep line ${out}/f1.out > ${out}/temp.out  # '2#grep' Temp file - "uncertain process"

grep line3 ${out}/f1.out > ${out}/f2.out  # '3#grep' Multi-Write error

grep ${unamestr} ${out}/f1.out > ${out}/f3.out   # '4#grep' Single error

grep  ${unamestr} ${out}/temp.out > ${out}/f2.out  # '5#grep' Multi-Write

rm ${out}/temp.out

grep line ${out}/f3.out > ${out}/f4.out   # '6#grep' transparent - No error
