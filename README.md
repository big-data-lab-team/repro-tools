![PyPI](https://img.shields.io/pypi/v/reprotools)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3553132.svg)](https://doi.org/10.5281/zenodo.3553132)
[![Build Status](https://travis-ci.org/big-data-lab-team/repro-tools.svg?branch=develop)](https://travis-ci.org/big-data-lab-team/repro-tools)
[![Coverage Status](https://coveralls.io/repos/github/big-data-lab-team/repro-tools/badge.svg?branch=develop)](https://coveralls.io/github/big-data-lab-team/repro-tools?branch=develop)

# repro-tools
A set of tools to evaluate the reproducibility of computations.

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Installation](#installation)
* [File Comparison](#file-comparison)
* [Process Labeling](#process-labeling)
* [Spot-tool](#spot-tool)
* [How to Contribute](#how-to-contribute)
* [License](#license)


## Installation

Simply install the package with `pip`

    $ pip install reprotools

Use parameter `--help` for additional info.


## File Comparison

`verifyFiles` script compares the output files produced by pipelines in different conditions. 
It identifies the files that are common to all conditions, and for these files, 
it compares them based on their checksums and other metrics configurable by file type.

### Usage

```
verifyFiles file_in output_file [-h] [-c CHECKSUMFILE] [-d FILEDIFF] [-m METRICSFILE] [-e EXCLUDEITEMS]
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

## Spot tool

Spot tool is a framework to automate the procedure of 
process labeling in the pipelines in two steps including: (1) capturing intermediary files (e.g. temp files)
(2) labeling the pipeline processes. `auto-peds` script creates a json file contains of all the process that create 
differences.

- Figure 3 shows the iterations of the Spot tool in a simple pipeline.

| ![Alt text](./reprotools/test/peds_test_data/iterative_modif.png?raw=true "Title") |
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

## How to Contribute

1. Clone repo and create a new branch: `$ git checkout https://github.com/big-data-lab-team/repro-tools -b name_for_new_branch`.
2. Make changes and test
3. Submit Pull Request with comprehensive description of changes


## License

[MIT](LICENSE) © /bin Lab