#!/usr/bin/env python
import os
import argparse


def check_file(parser, x):
    if x is None:
        parser.error('File is None')
    if os.path.exists(x):
        return x
    parser.error("File does not exist: {}".format(x))


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("file1", type=lambda x: check_file(parser, x))
    parser.add_argument("file2", type=lambda x: check_file(parser, x))
    args = parser.parse_args(args)
    diff = abs(os.path.getsize(args.file1) - os.path.getsize(args.file2))
    print(diff)
    return diff


if __name__ == '__main__':
    main()
