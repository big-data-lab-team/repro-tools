#!/usr/bin/env python

import argparse
import logging
import nibabel
import sys
import os
from PIL import Image
import numpy as np


def log_error(message):
    logging.error(message)
    sys.exit(1)


# Create a new image with the given size
def create_image(i, j):
    image = Image.new("RGB", (i, j), "white")
    return image


def main():
    parser = argparse.ArgumentParser(description="Computes a \
                                     checkerboard of the two images.")
    parser.add_argument("first_image_file")
    parser.add_argument("second_image_file")
    parser.add_argument("output_image_file")
    parser.add_argument("checkerboard_size")
    args = parser.parse_args()

    size = int(args.checkerboard_size)
    assert(size > 0)

    # check the image format
    if os.path.splitext(args.first_image_file)[1] in ['.png', '.jpg']:
        img1 = Image.open(args.first_image_file)
        img2 = Image.open(args.second_image_file)
        xdim, ydim = img1.size
        new = create_image(xdim, ydim)
        pixels = new.load()
        for x in range(0, xdim):
            for y in range(0, ydim):
                if (x/size + y/size) % 2 == 0:
                    pixel = img1.getpixel((x, y))
                    # make brownish color
                    pixels[x, y] = (pixel[0], int(pixel[1]/3), 0)
                else:
                    # (int(gray), int(gray), int(gray))
                    pixels[x, y] = img2.getpixel((x, y))
        new.save(args.output_image_file)
        sys.exit(0)

    # Load images using nibabel
    im1 = nibabel.load(args.first_image_file)
    im2 = nibabel.load(args.second_image_file)

    # Check that both images have the same dimensions
    shape1 = im1.header.get_data_shape()
    shape2 = im2.header.get_data_shape()
    if shape1 != shape2:
        log_error("Images don't have the same shape!")

    data1 = im1.get_data()
    data2 = im2.get_data()
    xdim = shape1[0]
    ydim = shape1[1]
    zdim = shape1[2]
    ssd = 0

    for x in range(0, xdim):
        for y in range(0, ydim):
            for z in range(0, zdim):
                if (x/size + y/size + z/size) % 2 == 0:
                    # take from image 1
                    pass
                else:  # take from image 2
                    data1[x][y][z] = data2[x][y][z]
    # That's it!
    nibabel.save(im1, args.output_image_file)


if __name__ == '__main__':
    main()
