[![Build Status](https://travis-ci.org/ali4006/repro-tools.svg?branch=develop)](https://travis-ci.org/ali4006/repro-tools)
[![Coverage Status](https://coveralls.io/repos/github/ali4006/repro-tools/badge.svg?branch=develop)](https://coveralls.io/github/ali4006/repro-tools?branch=develop)


# repro-tools
A set of tools to evaluate the reproducibility of computations.

## verifyFiles

verifyFiles.py compares the output files produced by pipelines in different conditions. It identifies the files that are common to all conditions, and for these files, it compares them based on their checksums and other metrics configurable by file type.

### Prerequisites

Python 2.7.5

## Running the verifyFiles.py script

```
usage:verifyFiles.py file_in output_file [-h] [-c CHECKSUMFILE] [-d FILEDIFF] [-m METRICSFILE] [-e EXCLUDEITEMS]
                     [-k CHECKCORRUPTION] [-s SQLITEFILE] [-x EXECFILE] [-t TRACKPROCESSES] [-i FILEWISEMETRICVALUE]

file_in,                                          Mandatory parameter.Directory path to the file containing the conditions.
output_file,                                      Json file format to keep output results.
-c,CHECKSUM FILE,       --checksumFile            Reads checksum from files. Doesn't compute checksums locally if this parameter is set.
-m METRICSFILE,         --metricsFile             CSV file containing metrics definition. Every line contains 4 elements: metric_name,file_extension,command_to_run,output_file_name
-e EXCLUDEITEMS,        --excludeItems            The path to the file containing the folders and files that should be excluded from creating checksums.
-k CHECKCORRUPTION,     --checkCorruption         The script verifies if any files are corrupted ,when this flag is set as true
-s SQLITEFILE,          --sqLiteFile              The path to the SQLITE file,having the reprozip trace details.
-x EXECFILE ,           --execFile                Writes the executable details to a file.
-t TRACK PROCESSES,     --trackProcesses          If this flag is set, it traces all the processes using reprozip to record the details and writes it into a csv with with the given name
-i FILEWISEMETRICVALUE, --filewiseMetricValue     Folder name on to which the individual filewise metric values are written to a csv file
```
### Test Cases
__Pytest syntax__
>pytest --cov=./ ./test_verifyFiles.py
## plot_matrix

`plot_matrix.py` plot heatmaps of difference matrices produced by
`verifyFiles.py`. For instance, `./plot_matrix.py
test/test_differences_plot.txt output.png` will produce the following
plot:

![Alt text](./reprotools/test/test_differences_plot.png?raw=true "Title")

`-t` argument gives the possibility to superimpose the predicted matrices achived by `predict.py` over the difference matrices produced by `verifyFiles.py`. For example, `python plot_matrix.py test/predict_test/test_differences.txt -t test/predict_test/triangular-S_0.6_test_data_matrix.txt test_plot_matrix.png` will make the following plot:  

![Alt text](./reprotools/test/test_plot_matrix.png?raw=true "Title")
___
## Predict

`predict.py` can be used to predict the elements of utility matrix M ij when following the sequential generating of elements is a concern.
(Ex. a comparison matrix of generated files from a same pipeline process in two different versions of an operating system) 

The sampling method options for fitting the training sets of the Alternating Least Square (ALS) are consist of:  
	- columns  
	- rows,random-real  
	- random-unreal  
	- diagonal (random picking of j from a uniform distribution)  
	- triangular-L (Random-triangle-L: fewer i, more j)  
	- triangular-S (Random-triangular-S: more i, fewer j)  
	- Bias 

### Prerequisites: 
Spark 2.2.0, Python 2.7.13

### Running the script:
  * `predict.py [utility matrix file][training ratio][training sampling method]`
___

## Pipelines Error Detection Script (PEDS)

The aim of `PEDS` is clustering processes and creating a graph model representation of all the processes which introduce errors in the pipeline
based on a dependency-file and a difference-matrix-file created by reprozip tool and `veryfyFiles.py` respectively.

### Prerequisites:

Graphviz , Boutiques and Docker modules

### Running the script:

```
usage: peds sqlite_db diff_file [-i IGNORE] [-g GRAPH] [-o OUTPUT_FILE] [-c CAPTURE_MODE]

sqlite_db,                    sqlite database file captured by reprozip tool include dependency files.
diff_file,                    A json file computed differences between pipeline results.
-i IGNORE,                    List of process names to ignore during classification.
-g GRAPH,                     Graph name in a dot file format to save as output. Also output graph will be rendered in a png file format as well.
-o OUTPUT_FILE,               Output path directory to keep the result files.
-c CAPTURE_MODE,              The script captures all temporary and multi-write files, when this flag is set as true.
```
  Note: We can use the following command, in order to create other file formats (e.g. svg, png and etc.) for the graph representation from dot file.

  * `dot -Tpng Graphmodel.dot -o Figure.png`

### Auto-PEDS script

In order to have a full automation of the procedure of error detection in the pipelines, we created `auto-peds.py` script.
Actually, we defined an automation from the first step, execution of the pipelines through Docker and Boutiques, to the error recognition process iteratively.
`auto-peds.py` creates a json file contains of all the processes which create error in the pipeline finally.

### Running the script:

```
usage: auto_peds output_directory [-c VERIFY_CONDITION] [-r VERIFY_OUTPUT] [-s SQLITE_DB] [-o PEDS_OUTPUT]
                 [-m CAPTURE_MODE] [-p CAP_CONDITION] [-d DESCRIPTOR] [-i INVOCATION] [-d2 DESCRIPTOR_COND2] [-i2 INVOCATION_COND2]

output_directory,             Output directory to keep result files.
-c VERIFY_CONDITION,          Directory path to the file containing the conditions.
-r VERIFY_OUTPUT,             Path to the verify_file result files.
-s SQLITE_D,                  sqlite database file captured by reprozip tool include dependency files.
-o PEDS_OUTPUT,               Json output file of peds script that contains process commands and file with error.
-m CAPTURE_MODE,              The script captures all temporary and multi-write files, when this flag is set as true.
-p CAP_CONDITION              Indicate specific pipeline execution to capture under which condition (e.g. first or second).
-d DESCRIPTOR                 Boutiques descriptor file of the first pipeline condition (e.g. Centos7).
-i INVOCATION                 Boutiques invocation file of the first pipeline condition (e.g. Centos7).
-d2 DESCRIPTOR_COND2          Boutiques descriptor file of the second pipeline condition (e.g. Centos6).
-i2 INVOCATION_COND2          Boutiques invocation file of the second pipeline condition (e.g. Centos6).
```

Figure shows the iteration of error recognition and the final graph produced by `auto-peds` script in a simple example.
![Alt text](./reprotools/test/peds_test_data/classification.png?raw=true "Title")
