#!/usr/bin/python

import subprocess
import sys
import fileinput
import csv
import re
import os.path

'''
Modification Step: In order to make appropriate file copy to fix processes artificially, 
first, we replace the current script with the main pipeline process that create errors.
after that, script will make a copy of file if arguments are the same with backup command-lines.
'''

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

if __name__ == '__main__':

# updated commands refer to the single processes that create errors
# common_cmd refers to the multi-write processes that create errors
   with open( "/home/ubuntu/PEDS/test/peds_test/updated_commands.txt", 'r') as cfile:
       commands = csv_parser(cfile)
   try:
       with open( "/home/ubuntu/PEDS/test/peds_test/common_cmd.txt", 'r')as multi_write_file:
           multi_write_commands = csv_parser(multi_write_file)
   except: multi_write_commands=[]

   input_arg_cmd = sys.argv[0]
   current_script_name = __file__
   if "modif_script.py" in current_script_name:
      for pipe_com, pipe_val in commands.items():
         pipeline_commad = pipe_com.split(' ')
         pipe_cmd = pipeline_commad[0].split('/')[-1:][0]

         # check the backup folder and then make cope from input_arg_cmd to that folder if doesn't exist
         my_path = 'backup_scripts/'+str(pipe_cmd)
         if os.path.exists(my_path)==False:
            bash_command = "cp " + str(which(pipeline_commad[0])) +" "+ "/home/ubuntu/PEDS/test/peds_test/backup_scripts/"+str(pipe_cmd)
            os.system(bash_command)
            bash_command = "sudo cp " + "/home/ubuntu/PEDS/bin/modif_script.py " + str(which(pipeline_commad[0]))
            os.system(bash_command)

   if "modif_script.py" not in current_script_name:
      i = 1
      cmd_name = current_script_name.split('/')[-1:][0]
      command = '/home/ubuntu/PEDS/test/peds_test/backup_scripts/'+str(cmd_name)
      while i<len(sys.argv):
         command += " "+sys.argv[i]
         i +=1
      os.system(command)
      
      proc_list = multi_write_commands.keys()
      counter = 0
      WD_ref = "/home/ubuntu/PEDS/test/peds_test/centos6/test/"
      WD_cur = "/home/ubuntu/PEDS/test/peds_test/centos7/test/"
      WD_ref_saved = "centos6_common_files/"
      WD_cur_save = "centos7_common_files/"
      for pipe_com, pipe_files in commands.items():
         check = False
         pipeline_commad = pipe_com.split(' ')
         
         counter +=1 ##
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
