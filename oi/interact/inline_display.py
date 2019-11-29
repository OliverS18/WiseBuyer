"""
This script is inspired by hitrjj's implementation
https://blog.csdn.net/u014636245/article/details/83661559
Much thanks.
"""


import os
import numpy as np


def _translate_color(r, g, b):
    rgb_bins = np.array([0, 95, 135, 175, 215, 255])
    gray_bins = np.array([8 + 10 * i for i in range(24)])

    query = np.array([r, g, b])

    rgb_distance = (query[:, np.newaxis] - rgb_bins[np.newaxis, :]) ** 2
    gray_distance = ((query[:, np.newaxis] - gray_bins[np.newaxis, :]) ** 2).sum(axis=0)

    rgb_candidate = np.argmin(rgb_distance, axis=1)
    rgb_distance = rgb_distance.min(axis=1).sum()

    gray_candidate = np.argmin(gray_distance)
    gray_distance = gray_distance.min()

    if rgb_distance < gray_distance:
        return 16 + (rgb_candidate * np.array([36, 6, 1])).sum()
    else:
        return 232 + gray_candidate


def img2terminal(img, width=None, height=None, ratio=2, indent=0):
    img = img[23:-23, 23:-23, :]                    # crop the padding

    w = img.shape[1]
    h = img.shape[0]

    width = width or os.get_terminal_size()[0] - 2 * indent

    scale = w // width

    if height:
        ratio = h * width / height / w * ratio

    strimg = ''
    line = 0

    for y in range(0, h, int(scale * ratio)):
        line += 1

        strline = ' ' * indent
        for x in range(0, w, scale):
            strline += "\033[48;5;%dm%s\033[0m" % (_translate_color(img[y, x, 2], img[y, x, 1], img[y, x, 0]), ' ')

        strimg += strline + '\n'

    print(strimg.strip('\n'))

    return line


def clear(line):
    command = '\033[{}A\r'.format(line)

    for _ in range(line):
        command += '\033[K\n\r'

    command += '\033[{}A\r'.format(line)

    print(command, end='')
