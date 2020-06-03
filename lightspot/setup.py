import sys
from setuptools import setup
import sys

VERSION = "0.0.1"
DEPS = [
       ]

setup(name="spottool",
      version=VERSION,
      description=(" A set of tools to evaluate the reproducibility "
                   "of computations "),
      url="https://github.com/big-data-lab-team/spot",
      author="Big Data Infrastructures for Neuroinformatics lab",
      classifiers=[
                "Programming Language :: Python",
                "Programming Language :: Python :: Implementation :: PyPy",
                "License :: OSI Approved :: MIT License",
                "Topic :: Software Development :: Libraries :: Python Modules",
                "Operating System :: OS Independent",
                "Natural Language :: English"
                  ],
      license="MIT",
      packages=["spot"],
      include_package_data=True,
      test_suite="pytest",
      tests_require=["pytest"],
      entry_points={
        "console_scripts": [
            "verify_files=spot:verify_files",
            "spottool=spot:spottool",
            "wrapper=spot:wrapper",

        ]
      },
      setup_requires=DEPS,
      install_requires=DEPS,
      zip_safe=False)
