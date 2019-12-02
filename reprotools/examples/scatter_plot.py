import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clss
import matplotlib.cm as cm
from sklearn.preprocessing import normalize
import csv
import seaborn as sns
import pandas as pd


def csv_reader(csv_file):
    # open csv file
    with open(csv_file, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        included_cols = [22, 26]
        freq_ = {}
        subjects = {}
        i = 0
        for row in reader:
            if i == 0:
                i = i+1
                continue
            subjects[int(row[26])] = [float(i) for i in row[1:21]]
            freq_[int(row[26])] = float(row[22])
    return freq_, subjects


def get_cmap(n, name='hsv'):
    return plt.cm.get_cmap(name, n)


def main():
    parser = argparse.ArgumentParser(description="Scatter plots of Dice \
                                     coefficients and region sizes.")
    parser.add_argument("csv_file",
                        help='Input CSV file')
    parser.add_argument("output",
                        help='Output folder')

    args = parser.parse_args()
    csv_file = args.csv_file

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

    fig = plt.figure(figsize=(30, 14))
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    # ax3 = fig.add_subplot(223)
    # ax4 = fig.add_subplot(224)

    data2 = pd.read_csv(csv_file)  # load data set
    data2.pop('0.0')
    col, row = data2.shape
    cmap = get_cmap(12)
    markers = ['o', 'v', '*', 'P']
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
    # [(a,b) for a,b in zip(markers, colors)]
    groups = [(k, j) for j in markers for k in colors]
    i = 1
    x2 = data2['2.0'][1::2]
    for d in data2.columns:
        list_ = data2[d]
        x, y = list_[1::2], np.round(list_[::2], 5)
        out = np.polyfit(x, y, 2)
        # x = [int(sum(x)/len(x))] * len(x)
        label_ = region_labels[float(d)]
        ax2.scatter(x, y, c='b', label=label_, marker='o')
        ax2.legend(loc='bottom right')
        ax2.set_xlabel('Region Size (voxels)', fontsize=22)
        ax2.set_ylabel('Dice Coefficients', fontsize=22)
        if int(sum(x)/len(x)) < 10000:
            ax1.scatter(x, y, c=groups[i][0], label=label_,
                        marker=groups[i][1])
            ax1.legend(loc='bottom right')
            ax1.set_xlabel('Region Size (voxels)', fontsize=22)
            ax1.set_ylabel('Dice Coefficients', fontsize=22)
            i = i + 1

    # plt.xlabel('Region Size (voxels)', fontsize=22)
    # plt.ylabel('Similarity (Dice coe)', fontsize=22)
    # plt.legend(loc='bottom right')
    # plt.xscale('log')
    plt.rc('axes', titlesize=48)
    plt.savefig(args.output+'scatter_plot.png', bbox_inches='tight')
#    plt.show()


if __name__ == '__main__':
    main()
