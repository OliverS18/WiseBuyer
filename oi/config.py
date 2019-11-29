"""
This file deals with the operation about configs. usually these files are stored under `configs/`
"""


import os
from easydict import EasyDict
import configparser


_CONFIG_NAME = 'v-0-1-2.ini'


def load_config() -> EasyDict:
    """
    This function load configurations for the service set-up procedure.

    :return: an EasyDict containing configs.
    """

    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'configs', _CONFIG_NAME))

    options = dict(parser)
    for section in options:
        options[section] = dict(options[section])

    return EasyDict(options)


cfg = load_config()
