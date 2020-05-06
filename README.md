![PyPI](https://img.shields.io/pypi/v/spottool)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3553132.svg)](https://doi.org/10.5281/zenodo.3553132)
[![Build Status](https://travis-ci.org/ali4006/spot.svg?branch=develop)](https://travis-ci.org/big-data-lab-team/spot)
[![Coverage Status](https://coveralls.io/repos/github/big-data-lab-team/spot/badge.svg?branch=develop)](https://coveralls.io/github/big-data-lab-team/spot?branch=develop)

# Spot-tool
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

Spot identifies the components in a pipeline, at the resolution
level of a system process, that produce different results in different
execution conditions.

### Usage

You must:
* Build Docker images for the pipelines in different conditions 
(e.g. CentOS6 and CentOS7) 
* Create Boutiques descriptor files 
for each condition (See [Boutiques](https://boutiques.github.io/) website)
* Get provenance information using ReproZip tool in one condition (Check [ReproZip](http://docs.reprozip.org/en/1.0.x/packing.html) docs)
* Refer to output directory of one condition as reference and the other one as base
* Set `output_directory` path including all the above mentioned files

To automatically find processes that create differences you must run the `auto_spot` command.
This creates a json file contains of all the processes that create differences.


Example of usage:
Run:
```
clone repository https://github.com/big-data-lab-team/spot.git
docker build -t spot_centos7_latest ./spot/example/centos7/subject1/
docker build -t spot_centos6_latest ./spot/example/centos6/subject1/

cd `./spot/example/`
auto_spot -d descriptor.json -i invocation.json -d2 descriptor_cond2.json
          -i2 invocation_cond2.json -s trace_test.sqlite3 -c conditions.txt -e exclude_items.txt
          -o commands.json <PATH_TO_OUTPUT>
```
You can now look at `commands.json` to see the processes that introduce differences in this example pipeline.

## How to Contribute

1. Clone repo and create a new branch: `$ git checkout https://github.com/big-data-lab-team/spot -b name_for_new_branch`.
2. Make changes and test
3. Submit Pull Request with comprehensive description of changes


## License

[MIT](LICENSE) © /bin Lab