![PyPI](https://img.shields.io/pypi/v/spottool)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3553132.svg)](https://doi.org/10.5281/zenodo.3553132)
[![Build Status](https://travis-ci.org/ali4006/spot.svg?branch=develop)](https://travis-ci.org/big-data-lab-team/spot)
[![Coverage Status](https://coveralls.io/repos/github/big-data-lab-team/spot/badge.svg?branch=develop)](https://coveralls.io/github/big-data-lab-team/spot?branch=develop)

# Spot
A set of tools to evaluate the reproducibility of computations.

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Installation](#installation)
* [Spot](#spot)
* [How to Contribute](#how-to-contribute)
* [License](#license)


## Installation

Simply install the package with `pip`

    $ pip install spottool

## Spot

Spot identifies the processes in a pipeline that produce different results in different
execution conditions.

### Usage

Pre-requisites:
* Install and start [Docker](http://www.docker.com)
* Build Docker images for the pipelines in different conditions (e.g. Debian10 and CentOS7) 
* Create [Boutiques](https://boutiques.github.io) descriptors for the pipeline, in each condition
* Get provenance information using [ReproZip](http://docs.reprozip.org/en/1.0.x/packing.html) tool in one condition

The `auto_spot` command finds processes that create differences in results obtained in different conditions and reports them in a JSON file.

Example of usage:

There is a simple example of how Spot tool works. In this example, we created docker images and descriptors for the distributions of Linux (CentOS 7 VS. Debian 10 (buster)), which run a bash script containing different lines of `grep` command. This script creates different output files depending on the OS name. Also, we acquired ReproZip traced file in CentOS 7.
If you follow the below instruction, you will produce two JSON files. One is `commands_captured_c.json` that stores processes with transient files. The other one is `commands.json` that stores processes that create differences in two attributes: multi-write processes (in `total_commands_multi`) and single write processes (in `total_commands`).

```
git clone https://github.com/big-data-lab-team/spot.git
cd spot
pip install .
cd spot/example/

docker build -t spot_centos_latest centos7/subject1/
docker build -t spot_debian_latest debian/subject1/

auto_spot -d descriptor.json -i invocation.json -d2 descriptor_cond2.json -i2 invocation_cond2.json -s trace_test.sqlite3 -c conditions.txt -e exclude_items.txt -o commands.json .
```

## How to Contribute

1. Clone repo and create a new branch: `$ git checkout https://github.com/big-data-lab-team/spot -b name_for_new_branch`.
2. Make changes and test
3. Submit Pull Request with comprehensive description of changes


## License

[MIT](LICENSE) © /bin Lab
