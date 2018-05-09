#!/usr/bin/python

import argparse
import subprocess
import sys
import fileinput
import csv
import re
import os.path

#Modification Step: In order to make appropriate file copy to fix processes artificially, 
#first, we replace the current script with the main pipeline process that create errors.
#after that, script will make a copy of file if arguments are the same with backup command-lines.

def is_intstring(s):
    try:
        float(s)
        return False
    except ValueError:
        return True

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

def csv_parser(cfile):
      command_parsed = {}
      for line in cfile:
         f_list = []
         command = str(line).split('##')[:1]
         command = str(command[0].replace('\x00' or ' ',' '))
         file_name = str(line).split('##')[1:]
         file_name = file_name[0][2:-3].replace("'",'')
         file_name_list = file_name.split(',')
         for file in file_name_list:
            count = 0
            for f in file.split('/'):
           #    if f == "exec":
               if f == "centos7":
                  count +=1
                  break
               else: count +=1
            f_list.append("/".join(file.split('/')[count:]))
         command_parsed[command]=f_list
      return command_parsed

def main(args=None):
#   parser = argparse.ArgumentParser(description="Script modifier")
#   parser.add_argument("updated_commands", action="store",
#                        help="Updated comments.")
#   parser.add_argument("common_cmd", action="store",
#                        help="Common cmd.")
#   results = parser.parse_args(args)

## set env: export PATH=to/my/backup/folder:$PATH
## set env: export reprotool=${PWD}
   WD = os.environ['reprotool']
   WD_test = os.environ['pedsfolder']
   # updated commands refer to the single processes that create errors
   # common_cmd refers to the multi-write processes that create errors
   with open(WD_test+'/total_commands.txt', 'r') as cfile:
       commands = csv_parser(cfile)
   try:
       with open(WD_test+'/common_cmd.txt', 'r')as multi_write_file:
           multi_write_commands = csv_parser(multi_write_file)
   except: multi_write_commands=[]
   proc_list = multi_write_commands.keys()

   input_arg_cmd = sys.argv[0]
   current_script_name = __file__

   i = 1
   cmd_name = current_script_name.split('/')[-1:][0]
   command = WD_test+'/backup_scripts/'+str(cmd_name)
   while i<len(sys.argv):
      command += " "+sys.argv[i]
      i +=1
   os.system(command)
      
   WD_ref = WD_test+"/centos6/test/"
   WD_cur = WD_test+"/centos7/test/"
   WD_ref_saved = WD_test+"/centos6_common_files/"
   WD_cur_save = WD_test+"/centos7_common_files/"
   for pipe_com, pipe_files in commands.items():
      check = False
      pipeline_commad = pipe_com.split(' ')
      file_name = str(pipeline_commad[0].split('/')[-1])+"_" ##
      if str(which(pipeline_commad[0])) == str(which(input_arg_cmd)):
         if len(pipeline_commad)-1 == len(sys.argv):
            check = True
            i = 1
            while i < len(sys.argv):
               if pipeline_commad[i] != sys.argv[i] and is_intstring(sys.argv[i]):
                  check=False
                  break 
               i +=1
      if check==True:
         for file in pipe_files:
            f_ = file.split('/')[-1] ##

            from_path = WD_ref + file
            To_path = WD_cur + file
            from_saved_path = WD_ref_saved + file_name + f_
            To_save_path = WD_cur_save + file_name + f_ ##

            if pipe_com in proc_list:
               bash_command = "cp " + from_saved_path + " " + To_save_path
               os.system(bash_command)
            my_bash_command = "cp " + from_path + " " + To_path
            os.system(my_bash_command)
         break
      else: continue

if __name__ == '__main__':
      main()
