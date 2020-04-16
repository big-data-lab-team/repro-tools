![PyPI](https://img.shields.io/pypi/v/spottool)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3553132.svg)](https://doi.org/10.5281/zenodo.3553132)
[![Build Status](https://travis-ci.org/ali4006/spot.svg?branch=develop)](https://travis-ci.org/ali4006/spot)
[![Coverage Status](https://coveralls.io/repos/github/big-data-lab-team/spot/badge.svg?branch=develop)](https://coveralls.io/github/big-data-lab-team/spot?branch=develop)

# repro-tools
A set of tools to evaluate the reproducibility of computations.

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Installation](#installation)
* [Spot-tool](#spot-tool)
* [How to Contribute](#how-to-contribute)
* [License](#license)


## Installation

Simply install the package with `pip`

    $ pip install spottool

## Spot tool

Spot tool is a framework to automate the procedure of 
finding processes that create differences in the pipeline in two steps including: (1) capturing transient files 
(2) labeling the pipeline processes. This creates a json file contains of all the processes that create 
differences.

### Prerequisites

sqlite3 , boutiques, docker, pandas, and numpy packages. 

### Usage

```
auto_spot output_directory [-c VERIFY_CONDITION] [-e EXCLUDE_ITEMS] [-s SQLITE_DB] [-m WRAPPER] 
          [-o SPOT_OUTPUT] [-d BASE_DESCRIPTOR] [-i BASE_INVOCATION] [-d2 REF_DESCRIPTOR] 
		  [-i2 REF_INVOCATION] [-r REFERENCE_COND] [-b BASE_COND]

output_directory,             Output directory to keep result files.
-c VERIFY_CONDITION,          Directory path to the file containing the conditions.
-e EXCLUDE_ITEMS,             The list of files/folders to be ignored.
-s SQLITE_D,                  SQLite database file created by reprozip tool include dependency files.
-m WRAPPER,                   Path to the wrapper script that should be replaced with the original pipeline execution files.
-o SPOT_OUTPUT,               Json output file of spot script that contains process commands and file with differences.
-d DESCRIPTOR,                Boutiques descriptor file of the first pipeline condition (e.g. Centos7).
-i INVOCATION,                Boutiques invocation file of the first pipeline condition (e.g. Centos7).
-d2 DESCRIPTOR_COND2,         Boutiques descriptor file of the second pipeline condition (e.g. Centos6).
-i2 INVOCATION_COND2,         Boutiques invocation file of the second pipeline condition (e.g. Centos6).
-r REFERENCE_COND,            Path to the result files of the reference condition to capture intransient files.
-b BASE_COND,                 Path to the result files of the base condition.
``` 

## How to Contribute

1. Clone repo and create a new branch: `$ git checkout https://github.com/big-data-lab-team/spot -b name_for_new_branch`.
2. Make changes and test
3. Submit Pull Request with comprehensive description of changes


## License

[MIT](LICENSE) © /bin Lab