[![Build Status](https://travis-ci.org/ali4006/repro-tools.svg?branch=develop)](https://travis-ci.org/ali4006/repro-tools)
[![Coverage Status](https://coveralls.io/repos/github/ali4006/repro-tools/badge.svg?branch=develop)](https://coveralls.io/github/ali4006/repro-tools?branch=develop)


# repro-tools
A set of tools to evaluate the reproducibility of computations.

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [File Comparison](#file-comparison)
* [Predict Differences](#predict-differences)
* [Plot Differences](#plot-differences)
* [Process Labeling](#process-labeling)
* [NURM-tool](#nurm-tool)
* [License](#license)


## File Comparison

`verifyFiles` script compares the output files produced by pipelines in different conditions. 
It identifies the files that are common to all conditions, and for these files, 
it compares them based on their checksums and other metrics configurable by file type.

### Usage

```
verifyFiles.py file_in output_file [-h] [-c CHECKSUMFILE] [-d FILEDIFF] [-m METRICSFILE] [-e EXCLUDEITEMS]
               [-k CHECKCORRUPTION] [-s SQLITEFILE] [-x EXECFILE] [-t TRACKPROCESSES] [-r ONECONDITION]

file_in,                                          Mandatory parameter.Directory path to the file containing the conditions.
output_file,                                      JSON file format to keep output results.
-c,CHECKSUM FILE,       --checksumFile            Reads checksum from files. It doesn't compute checksums locally if this parameter is set.
-m METRICSFILE,         --metricsFile             CSV file containing metrics definition. Every line contains 4 elements: metric_name,file_extension,command_to_run,output_file_name
-e EXCLUDEITEMS,        --excludeItems            The path to the file containing the folders and files that should be excluded from creating checksums.
-k CHECKCORRUPTION,     --checkCorruption         The script verifies if any files are corrupted when this flag is set as true
-s SQLITEFILE,          --sqLiteFile              The path to the SQLite file, having the reprozip trace details.
-x EXECFILE ,           --execFile                Writes the executable details to a file.
-t TRACK PROCESSES,     --trackProcesses          If this flag is set, it traces all the processes using reprozip to record the details and writes it into a CSV with the given name
-r ONECONDITION,        --one_condition           List files and thier MD5 values on one condition without any comparison
```

## Predict Differences

`predict` script can be used to predict the elements of utility matrix M ij when following the sequential generating of elements is a concern.
(Ex. a comparison matrix of generated files from a same pipeline process in two different versions of an operating system) 

The sampling method options for fitting the training sets of the Alternating Least Square (ALS) are consist of:  
	- columns  
	- rows,random-real  
	- random-unreal  
	- diagonal (random picking of j from a uniform distribution)  
	- triangular-L (Random-triangle-L: fewer i, more j)  
	- triangular-S (Random-triangular-S: more i, fewer j)  
	- Bias 

### Prerequisites
Spark 2.2.0, Python 2.7.13

### Usage
```
predict.py matrix_file training_ratio approach dataset sampling_method 
           [-p PREDICTIONS] [-r RANDOM-RATIO-ERROR] [-s SEED-NUMBER]

matrix_file,                                         The matrix file produced by verifyFiles. Each line must be formated as '<file_id>;<condition_id>;<value>'.
training_ratio,                                      The ratio of matrix elements that will be added to the training set. Has to be in [0,1].
approach,                                            Prediction strategy: ALS, ALS-Bias or Bias.
dataset,                                             Name of the dataset. Just to be used in the name of the output files.
sampling_method,                                     Sampling method to use to build the training set.
-p PREDICTIONS,           --predictions              Text file where the predictions will be stored.
-r RANDOM-RATIO-ERROR,    --random-ratio-error       Maximum acceptable difference between target and effective training ratios.Defaults to 0.01.
-s SEED-NUMBER,           --seed_number              set seed number.
```


## Plot Differences

`plot_matrix` script plots heatmap of difference matrices produced by
`verifyFiles` script. 

### Usage
```
plot_matrix.py original_matrix output_file [-t TEST-MATRIX]

original_matrix,                                  Matrix file to plot. Each row should be in the following format: <ignored> <subject_id>  <binary_difference> <file_id>. File ids should be ordered according to their latest modification time.
output_file,                                      Output file where the plot will be saved. File type is determined from extension.
-t TEST-MATRIX,           --test_matrix            Matrix file to plot. Each row should be in the following format: <file_id> <subject_id> <ignored> <predic_value>.
File ids should be ordered according to their latest modification time.
```

* `-t` argument gives the possibility to superimpose the predicted matrices achived by `predict.py` 
over the difference matrices produced by `verifyFiles.py`.

### Examples

- `./plot_matrix.py test/test_differences_plot.txt output.png` (Figure 1)
- `python plot_matrix.py test/predict_test/test_differences.txt -t test/predict_test/triangular-S_0.6_test_data_matrix.txt test_plot_matrix.png` (Figure 2)

| ![Alt text](./reprotools/test/test_differences_plot.png?raw=true "Figure 1") | ![Alt text](./reprotools/test/test_plot_matrix.png?raw=true "Figure 2") |
|:---:|:---:|
| **Figure 1** | **Figure 2** | 

## Process Labeling

`peds` script labels the processes in the pipeline into three categories: 
1. Process that create differences
2. Transparent process
3. Undetermined process

This script works based on the file dependencies created by reprozip tool and 
the difference file created by veryfyFiles script.

### Usage

```
peds sqlite_db diff_file [-i IGNORE] [-o OUTPUT_FILE] [-c CAPTURE_MODE] [-a COMMAND_LINE]

sqlite_db,                    sqlite database file captured by reprozip tool include dependency files.
diff_file,                    A json file computed differences between pipeline results.
-i IGNORE,                    List of process names to ignore during labeling.
-o OUTPUT_FILE,               Output path directory to keep the result files.
-c CAPTURE_MODE,              The script captures all temporary and multi-write files, when this flag is set as true.
-a COMMAND_LINE,              Pass the command line executed in the pipeline to capture data that write differences.
```

## NURM tool

The Numerical Reproducibility Measurement (NURM) tool is a framework to automate the procedure of 
process labeling in the pipelines in two steps including: (1) capturing intermediary files (e.g. temp files)
(2) labeling the pipeline processes. `auto-peds` script creates a json file contains of all the process that create 
differences.

- Figure 3 shows the iterations of the NURM-tool in a simple pipeline.

| ![Alt text](./reprotools/test/peds_test_data/classification.png?raw=true "Title") |
|:---:|
| **Figure 3** |

### Prerequisites

sqlite3 , boutiques, docker, pandas, and numpy packages. 

### Usage

```
auto_peds output_directory [-c VERIFY_CONDITION] [-e EXCLUDE_ITEMS] [-s SQLITE_DB] [-m MODIF_SCRIPT] 
          [-o PEDS_OUTPUT] [-d BASE_DESCRIPTOR] [-i BASE_INVOCATION] [-d2 REF_DESCRIPTOR] 
		  [-i2 REF_INVOCATION] [-r REFERENCE_COND] [-b BASE_COND]

output_directory,             Output directory to keep result files.
-c VERIFY_CONDITION,          Directory path to the file containing the conditions.
-e EXCLUDE_ITEMS,             The list of files/folders to be ignored.
-s SQLITE_D,                  SQLite database file created by reprozip tool include dependency files.
-m MODIF_SCRIPT,              Path to the python script that should be replaced by the original pipeline execution files.
-o PEDS_OUTPUT,               Json output file of peds script that contains process commands and file with differences.
-d DESCRIPTOR,                Boutiques descriptor file of the first pipeline condition (e.g. Centos7).
-i INVOCATION,                Boutiques invocation file of the first pipeline condition (e.g. Centos7).
-d2 DESCRIPTOR_COND2,         Boutiques descriptor file of the second pipeline condition (e.g. Centos6).
-i2 INVOCATION_COND2,         Boutiques invocation file of the second pipeline condition (e.g. Centos6).
-r REFERENCE_COND,            Path to the output files of the reference condition to capture temp and multi-write files. Also, it make copies FROM this directory.
-b BASE_COND,                 Path to the output files of the base condition that make copies TO this directory.
``` 

## License
