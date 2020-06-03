#!/usr/bin/env python

import argparse
import nibabel
import os.path as op


def main():
    parser = argparse.ArgumentParser(description="Print image information")
    parser.add_argument("image_file")
    args = parser.parse_args()

    # Load images using nibabel
    assert(op.exists(args.image_file)), 'Cannot find file {}' \
                                        .format(args.image_file)
    im1 = nibabel.load(args.image_file)

    # Print image info
    print("Image shape is: {}".format(im1.header.get_data_shape()))
    print("Image type is: {}".format(im1.header.get_data_dtype()))
    print("Image voxel size in mm is: {}".format(im1.header.get_zooms()))


if __name__ == '__main__':
    main()
