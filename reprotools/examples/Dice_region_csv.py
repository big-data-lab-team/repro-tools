#!/usr/bin/env python

import argparse
import logging
import nibabel
import sys
import os.path as op
import numpy as np
import numpy.ma as ma
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import csv
# from dask import delayed
# import dask.array as da


def log_error(message):
    logging.error(message)
    sys.exit(1)


def remove_uncommons(regions2, regions, voxels_2):
    uncommon2 = np.setdiff1d(regions2, regions).tolist()
    for i in uncommon2:
        ind = np.where(regions2 == i)[0].tolist()[0]
        regions2 = np.delete(regions2, ind)
        voxels_2 = np.delete(voxels_2, ind)
    return regions2, voxels_2


def main():
    parser = argparse.ArgumentParser(description="Computes Dice coefficient \
                                     of the regions between images.")
    parser.add_argument("first_image",
                        help='First input T1W segmented image like aseg.nii')
    parser.add_argument("second_image",
                        help='Second input T1W segmented image like aseg.nii')
    parser.add_argument("output",
                        help='Output CSV file')

    args = parser.parse_args()
    output = args.output
    # Load images using nibabel
    im1 = nibabel.load(args.first_image)
    im2 = nibabel.load(args.second_image)

    # Check that both images have the same dimensions
    shape1 = im1.header.get_data_shape()
    shape2 = im2.header.get_data_shape()
    data1 = im1.get_data()
    data2 = im2.get_data()
    subj_info = {}
    voxel_counts = {}

    region_labels = {0: 'Background', 42: 'Right-Cerebral-Cortex',
                     3: ' Left-Cerebral-Cortex',
                     41: 'Right-Cerebral-White-Matter',
                     2: 'Left-Cerebral-White-Matter',
                     47: 'Right-Cerebellum-Cortex',
                     8: 'Left-Cerebellum-Cortex',
                     16: 'Brain-Stem', 46: 'Right-Cerebellum-White-Matter',
                     7: 'Left-Cerebellum-White-Matter',
                     10: 'Left-Thalamus-Proper*',
                     49: 'Right-Thalamus-Proper*',
                     4: 'Left-Lateral-Ventricle', 51: 'Right-Putamen',
                     12: 'Left-Putamen', 43: 'Right-Lateral-Ventricle',
                     17: 'Left-Hippocampus', 53: 'Right-Hippocampus',
                     60: 'Right-VentralDC', 28: 'Left-VentralDC',
                     50: 'Right-Caudate', 11: 'Left-Caudate',
                     54: 'Right-Amygdala', 18: 'Left-Amygdala',
                     52: 'Right-Pallidum', 63: 'Right-choroid-plexus',
                     13: 'Left-Pallidum', 31: 'Left-choroid-plexus',
                     15: '4th-Ventricle', 77: 'WM-hypointensities',
                     24: 'CSF', 251: 'CC_Posterior', 255: 'CC_Anterior',
                     58: 'Right-Accumbens-area', 14: '3rd-Ventricle',
                     26: 'Left-Accumbens-area', 253: 'CC_Central',
                     254: 'CC_Mid_Anterior', 252: 'CC_Mid_Posterior',
                     85: 'Optic-Chiasm', 5: 'Left-Inf-Lat-Vent',
                     44: 'Right-Inf-Lat-Vent', 62: 'Right-vessel',
                     30: 'Left-vessel', 80: 'non-WM-hypointensities',
                     72: '5th-Ventricle'}
    # x1 = da.from_array(data1, chunks=(30,30,30))
    # p1 = da.unique(x1, return_counts=True)
    # regions = p1[0].compute()
    # voxels_1 = p1[1].compute().astype('float')
    # print("unique numbers: ", p1[0].compute())
    # print("counts the numbers: ", p1[1].compute())
    regions, voxels_1 = np.unique(data1, return_counts=True)
    voxels_1 = voxels_1.astype('float')
    regions2, voxels_2 = np.unique(data2, return_counts=True)
    voxels_2 = voxels_2.astype('float')

    if op.exists(output):
        with open(output, 'r') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            common_regions = list(csv_reader)[0]
            list_id = []
            for key in common_regions:
                list_id.append(region_labels.keys()[
                                     region_labels.values().index(key)])
            regions2, voxels_2 = remove_uncommons(regions2, np.array(list_id),
                                                  voxels_2)

    regions2, voxels_2 = remove_uncommons(regions2, regions, voxels_2)
    regions, voxels_1 = remove_uncommons(regions, regions2, voxels_1)

    diff = abs(voxels_1 - voxels_2)
    dice_values = np.round(abs(((voxels_1 + voxels_2) -
                           2*diff))/(voxels_1 + voxels_2), 5)
    dice_values = np.ndarray.tolist(dice_values)
    print(sum(dice_values)/len(dice_values))
    regions = np.ndarray.tolist(regions)
    for ind, val in enumerate(regions):
        subj_info[region_labels[val]] = dice_values[ind]
        voxel_counts[region_labels[val]] = int((voxels_1[ind] +
                                                voxels_2[ind])/2)

    # csv_columns = []
    # for i, v in enumerate(subj_info.keys()):
    #     csv_columns.append(region_labels[v])
    csv_columns = subj_info.keys()
    if op.exists(output):
        with open(output, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writerow(subj_info)
            writer.writerow(voxel_counts)
    else:
        with open(output, 'w+') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerow(subj_info)
            writer.writerow(voxel_counts)

    # with open(output, 'a') as f:
    #     for key in subj_info.keys():
    #         f.write("%s,%s\n"%(key,subj_info[key]))

    # csv_columns = list(map(str, subj_info.keys()))
    # with open(output, 'w+') as csvfile:
    #     writer = csv.DictWriter(csvfile, subj_info.values())
    #     writer.writerow(subj_info)

    # x_diff = da.from_array(data_diff, chunks=(30,30,30))
    # p_diff = da.unique(x_diff, return_counts=True)
    # print("unique numbers: ", p_diff[0].compute())
    # print("counts the numbers: ", p_diff[1].compute())

    print("DONE!")


if __name__ == '__main__':
    main()
