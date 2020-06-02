#!/usr/bin/env bash

if [ $# != 2 ]
then
echo "usage: $0 <input_file.txt> <output_folder>"
exit 1
fi

input_file=$1
out=$2

# Set env variables
. /etc/os-release
unamestr="$(echo $NAME | tr ' ' .)"

if [ "$unamestr" = "Debian.GNU/Linux" ]; then
unamestr=12345
elif [ "$unamestr" = "CentOS.Linux" ]; then
unamestr=67890
fi

grep ${unamestr} ${input_file} > ${out}/f1.out   # 1)Create different files

grep line ${out}/f1.out > ${out}/temp.out  # 2)Create temp file without diff

grep line3 ${out}/f1.out > ${out}/f2.out  # 3) Create multi-write file with diff

grep  ${unamestr} ${out}/temp.out > ${out}/f2.out  # 4) Create multi-write file without diff

grep line2 ${out}/f2.out > ${out}/f3.out   # 5) Create transparent file

rm ${out}/temp.out
