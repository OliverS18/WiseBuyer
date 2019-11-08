"""
This file deals with the operation about configs. usually these files are stored under `configs/`
"""


import os
from easydict import EasyDict
import configparser


_CONFIG_NAME = 'test.ini'


def load_config() -> EasyDict:
    """
    This function load configurations for the service set-up procedure.

    :return: an EasyDict containing configs.
    """

    parser = configparser.ConfigParser()
    options = parser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'configs', _CONFIG_NAME))

    return EasyDict(options)


cfg = load_config()
