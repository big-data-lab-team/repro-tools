import sys
from setuptools import setup
import sys

VERSION = "0.0.1"
DEPS = ["pandas", "graphviz"]

setup(name="reprotool",
      version=VERSION,
      description="",
      url="https://github.com/big-data-lab-team/repro-tools",
      author="",
      classifiers=[
                "Programming Language :: Python",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.4",
                "Programming Language :: Python :: 3.5",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: Implementation :: PyPy",
                "Topic :: Software Development :: Libraries :: Python Modules",
                "Operating System :: OS Independent",
                "Natural Language :: English"
                  ],
      license="",
      include_package_data=True,
      test_suite="pytest",
      tests_require=["pytest"],
      setup_requires=["commands","pandas","graphviz"],
      install_requires=DEPS,
      zip_safe=False)
