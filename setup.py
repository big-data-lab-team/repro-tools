import sys
from setuptools import setup
import sys

VERSION = "0.0.1"
DEPS = [
         "graphviz",
         "pandas",
         "matplotlib",
         "boutiques",
         "docker",
         "pyspark"
       ]

setup(name="reprotools",
      version=VERSION,
      description=(" A set of tools to evaluate the reproducibility "
                   "of computations "),
      url="https://github.com/big-data-lab-team/repro-tools",
      author="Big Data Infrastructures for Neuroinformatics lab",
      classifiers=[
                "Programming Language :: Python",
                "Programming Language :: Python :: 2",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 2.7",
                "Programming Language :: Python :: 3.4",
                "Programming Language :: Python :: 3.5",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: Implementation :: PyPy",
                "License :: OSI Approved :: MIT License",
                "Topic :: Software Development :: Libraries :: Python Modules",
                "Operating System :: OS Independent",
                "Natural Language :: English"
                  ],
      license="MIT",
      packages=["reprotools"],
      include_package_data=True,
      test_suite="pytest",
      tests_require=["pytest"],
      entry_points={
        "console_scripts": [
            "verify_files=reprotools:verify_files",
            "peds=reprotools:peds",
            "auto_peds=reprotools:auto_peds",
            "plot_matrix=reprotools:plot_matrix",
            "predict=reprotools:predict"
        ]
      },
      setup_requires=DEPS,
      install_requires=DEPS,
      zip_safe=False)
