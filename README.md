![PyPI](https://img.shields.io/pypi/v/spottool)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3553132.svg)](https://doi.org/10.5281/zenodo.3553132)
[![Build Status](https://travis-ci.org/ali4006/spot.svg?branch=develop)](https://travis-ci.org/big-data-lab-team/spot)
[![Coverage Status](https://coveralls.io/repos/github/big-data-lab-team/spot/badge.svg?branch=develop)](https://coveralls.io/github/big-data-lab-team/spot?branch=develop)

# Spot

Spot identifies the processes in a pipeline that produce different results in different
execution conditions.

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Installation](#installation)
* [Spot](#spot)
* [How to Contribute](#how-to-contribute)
* [License](#license)


## Installation

Simply install the package with `pip`

    $ pip install spottool

## Pre-requisites

* Install and start [Docker](http://www.docker.com)
* Build Docker images for the pipelines in different conditions (e.g. Debian10 and CentOS7) 
* Create [Boutiques](https://boutiques.github.io) descriptors for the pipeline, in each condition
* Get provenance information using [ReproZip](http://docs.reprozip.org/en/1.0.x/packing.html) tool in one condition

The `auto_spot` command finds processes that create differences in results obtained in different conditions and reports them in a JSON file.

## Usage example

In this example, we run a bash script that calls the `grep` command
multiple times, creating different output files when run on different 
OSes. We use `spot` to compare the outputs obtained in CentOS 7 and Debian 10.

The example can be run using the following commands:
```
git clone https://github.com/big-data-lab-team/spot.git
cd spot
pip install .

docker build . -f spot/example/centos7/Dockerfile -t spot_centos_latest
docker build . -f spot/example/debian/Dockerfile -t spot_debian_latest

cd spot/example 

auto_spot -d descriptor_centos7.json -i invocation_centos7.json -d2 descriptor_debian10.json -i2 invocation_debian10.json -s trace_test.sqlite3 -c conditions.txt -e exclude_items.txt -o commands.json .
```

In this command:
* `descriptor_<distro>.json` is the Boutiques descriptor of the application executed in OS `<distro>`.
* `invocation_<distro>.json` is the Boutiques invocation of the application executed in OS `<distro>`, containing the input files.
* `trace_test.sqlite3` is a ReproZip trace of the application, acquired in CentOS 7.
* `condition.txt` is a text file that each line is the path to the output folder for each condition.
* `exclude_items.txt` is a text file, containing the list of items to be ignored while parsing the files and directories.

The command produces the following outputs:
*  `commands_captured_c.json` contains the list of processes with transient files. 
*  `commands.json` contains the list of processes that create differences in two attributes: multi-write
processes (in `total_commands_multi`) and single write processes (in
`total_commands`).

## How to Contribute

1. Clone repo and create a new branch: `$ git checkout https://github.com/big-data-lab-team/spot -b name_for_new_branch`.
2. Make changes and test
3. Submit Pull Request with comprehensive description of changes


## License

[MIT](LICENSE) © /bin Lab
