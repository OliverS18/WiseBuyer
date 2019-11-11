"""
This file takes the json-ed string and stylized them into dicts which can be processed by the rest part of the project.
"""


import os
import json
from typing import *
from easydict import EasyDict

from rules.crit import Reward
from rules.discount import Discount


def input_json(cart_json: str, user_json: str) -> Tuple[Dict, Dict, Dict, Dict, Dict, Dict, Dict, EasyDict]:
    """
    This function takes in all the information represented as json serialized strings, and then distribute them into
    multiple dicts used in different scenario.

    :param cart_json: path to a json path parsed from web representing information of commodities.
        there would be two part forming the list carried by the json string:
        [{commodity_dict}, {shop_name: coupon_schemes}]
        a typical item of the commodity dict would be like:
        {commodity_name: [original_price, discounted_price, preferred_amount, coupon_scheme, shop_name]}.
    :param user_json: path to a json path parsed from the user interface representing user-defined arguments.
        there would be two part forming the list carried by the json string:
        [{algorithm_options_name: corresponding_value}, {commodity_name: want_score}]

    :return: a list of dict containing discounted price, desired amount, commodity-wise discount in currency (rather
        than percentage), want score, coupon_scheme of each commodity, shop of each commodity, coupon_scheme of each
        shop as well as the options for algorithms (as easydict).
    """

    cart_dict, shop_coupon = json.load(open(cart_json))
    option, want = json.load(open(user_json))

    price = dict()
    amount = dict()
    discount = dict()
    scheme = dict()
    shop = dict()

    for commodity, data in cart_dict.items():
        price[commodity] = data[1]
        amount[commodity] = data[2]
        discount[commodity] = data[0] - data[1]
        scheme[commodity] = tuple(data[3])
        shop[commodity] = data[4]

    amount['*STOP*'] = 1

    shop_coupon = {shop_name: [tuple(shop_scheme) for shop_scheme in shop_schemes] + [(0, 0)]
                   for shop_name, shop_schemes in shop_coupon.items()}

    return price, amount, discount, want, scheme, shop, shop_coupon, EasyDict(option)


def output_json(strategies: List[Tuple], cache_path: str, commentator: Reward):
    """
    This function saves the proposed strategy into a json file.

    :param strategies: a list of strategies. each item within the list should follow the format as:
            ([commodity_name], strategy_score)
    :param commentator: a reward object used to be called to acquire enriched description about the given strategies
    :param cache_path: the temp path to place the output json file
    """

    enriched = commentator.summarize(strategies)
    json.dump(enriched, open(cache_path, 'w', encoding='utf-8'), ensure_ascii=False)
