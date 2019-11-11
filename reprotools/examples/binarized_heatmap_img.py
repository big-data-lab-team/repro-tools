#!/usr/bin/env python

import argparse
import logging
import nibabel
import sys
import numpy as np
import numpy.ma as ma
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl


def log_error(message):
    logging.error(message)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Computes a \
                                     binarized heatmap of the images.")
    parser.add_argument("binary_sum_image_file",
                        help='Input sum of binary of images like T1W images')
    parser.add_argument("output_image_file",
                        help='output folder')
    parser.add_argument("ref_image_file",
                        help='reference image like MNI-152')

    args = parser.parse_args()

    # Load images using nibabel
    im1 = nibabel.load(args.binary_sum_image_file)
    im_ref = nibabel.load(args.ref_image_file)

    # Check that both images have the same dimensions
    shape1 = im1.header.get_data_shape()
    shape2 = im_ref.header.get_data_shape()
    # 260, 311, 260
    # 129, 155, 130
    startcolor = '#ff0000'
    midcolor = '#990033'
    midcolor2 = '#ffff00'
    endcolor = '#FFFFFF'
    own_cmap1 = mpl.colors.LinearSegmentedColormap.from_list(
                    'own2', [midcolor, midcolor2, endcolor])
    fig = plt.figure(figsize=(25, 10))
    ax1 = fig.add_subplot(131)
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)
    plt.subplots_adjust(hspace=0.05, wspace=0.005)

    cbar_ax = fig.add_axes([.91, .2, .02, .6])
    cbar_ax.tick_params(labelsize=26)

    data1 = im1.get_data()
    im_data_ref = im_ref.get_data()

    hor_view = data1[129, :, :]
    hor_view_ref = im_data_ref[98, :, :]
    ver_view = data1[:, 155, :]
    ver_view_ref = im_data_ref[:, 116, :]
    axi_view = data1[:, :, 130]
    axi_view_ref = im_data_ref[:, :, 94]

    own_cmap1.set_under("0.5", alpha=0)
    hmax = sns.heatmap(np.rot90(ver_view), cbar_ax=cbar_ax, cmap=own_cmap1,
                       xticklabels='', yticklabels='', ax=ax3, vmin=1, vmax=7)
    hmax.imshow(np.rot90(ver_view_ref), cmap='gray', aspect=hmax.get_aspect(),
                extent=hmax.get_xlim() + hmax.get_ylim())

    hmax2 = sns.heatmap(np.rot90(hor_view), cmap=own_cmap1, xticklabels='',
                        yticklabels='', cbar=False, ax=ax2, vmin=1, vmax=8)
    hmax2.imshow(np.rot90(hor_view_ref), cmap='gray',
                 aspect=hmax2.get_aspect(),
                 extent=hmax2.get_xlim() + hmax2.get_ylim())

    hmax3 = sns.heatmap(np.rot90(axi_view), cmap=own_cmap1, xticklabels='',
                        yticklabels='', cbar=False, ax=ax1, vmin=1, vmax=8)
    hmax3.imshow(np.rot90(axi_view_ref), cmap='gray',
                 aspect=hmax3.get_aspect(),
                 extent=hmax3.get_xlim() + hmax3.get_ylim())

    plt.savefig('binarized.png', bbox_inches='tight')
#    plt.show()

    # sns.heatmap(frequency_matrix, cbar=first == 0,
    #         cbar_ax=None if first else cbar_ax, vmin=0, vmax=1,
    #         annot=np.array(heatmap_label), fmt='',
    #         annot_kws=my_annot_kws, linewidths=2,
    #         xticklabels='', yticklabels='', cmap=own_cmap1,
    #         ax=axes[j, i])

    # nibabel.save(im1, args.output_image_file)


if __name__ == '__main__':
    main()
