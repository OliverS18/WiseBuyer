"""
This file indicates the rules of e-commodity discounts by rewrite relevant method of MCTS nodes.
"""


from abc import ABC
from typing import *
from algorithms.mcts import TreeNode


class Discount(ABC):
    """
    This class defines the discount rule and reserve a __call__ API.
    """

    def __init__(self, price: Dict, modifier: Optional[Callable[[Dict, List], Dict]] = None, *args, **kwargs):
        """
        Instantiate an object recording the commodities' price info.

        :param price: a dict mapping from the name of commodities to their prices.
        :param modifier: a function taking original prices and bought commodities as input and update the price info.
        :param args: not used positional argument making compatible among descendants
        :param kwargs: not used keyword argument making compatible among descendants
        """

        self.price = price
        self.modifier = modifier

    def __call__(self, prev: Optional[TreeNode], action: str) -> float:
        """
        The API to be called by the TreeNode object.

        :param prev: the parent node of current considered node.
        :param action: the commodity bought of current node.

        :return: discounted total price up now.
        """

        raise NotImplementedError

    def sum(self, choices: List) -> float:
        """
        The API calling __call__ using a list of choices.

        :param choices: a list of commodity names
        :return: discounted total price of the given strategy.
        """

        pseudo_node = TreeNode(prehistory=choices)
        return self(pseudo_node, '*STOP*')


class SchemewiseDiscount(Discount, ABC):
    """
    This is the base class for all discount schemes that have a global coupon offer (which is usually in the form of
     `save x every y`).
    """

    def __init__(self, scheme_of_commodities: Dict, *args, **kwargs):
        """
        Instantiate an object representing multiple discount logics simultaneously.

        :param scheme_of_commodities: a mapping from commodities' name to its discount scheme (represented as tuple
            (save, every)).
        :param args: positional arguments passed to the parent class
        :param kwargs: keyword arguments passed to the parent class
        """

        super().__init__(*args, **kwargs)

        self.schemes = scheme_of_commodities
        self.scheme_types = set(self.schemes.values())

    def get_schemewise_coupon_and_cost(self, prev: Optional[TreeNode], action: str) -> Tuple[Dict, Dict]:
        """
        An API for easily getting coupon and cost of each discount scheme.

        :param prev: a tree node object representing the choice status (back to last commodity selected)
        :param action: current selected commodity

        :return: two dicts mapping schemes (in representation of tuple `(save, every)`) to the total got coupons and
            total costs respectively.
        """

        cost_by_scheme = {scheme_type: 0 for scheme_type in self.scheme_types}

        if prev is not None:
            for commodity in prev.history:
                cost_by_scheme[self.schemes[commodity]] += self.price[commodity]

        if action != '*STOP*':
            cost_by_scheme[self.schemes[action]] += self.price[action]

        coupon_by_scheme = dict()
        for scheme_type, total in cost_by_scheme.items():
            coupon_by_scheme[scheme_type] = (total // scheme_type[1]) * scheme_type[0]

        return coupon_by_scheme, cost_by_scheme


class ShopwiseDiscount(Discount, ABC):
    """
    This is the base class for all discount schemes that have coupon offers each shops (which is usually in the form of
     `save x after reaching y`).
    """

    def __init__(self, shop_of_commodities: Dict, shopwise_coupon: Dict, *args, **kwargs):
        """
        Instantiate an object representing discount logics of each shop simultaneously.

        :param shop_of_commodities: a mapping from commodities' name to its shop's name.
        :param args: positional arguments passed to the parent class
        :param kwargs: keyword arguments passed to the parent class
        """

        super().__init__(*args, **kwargs)

        self.shops = shop_of_commodities
        self.shop_types = set(self.shops.values())

        self.shopwise_coupon = {shop: sorted(coupons, key=lambda scheme: scheme[0])
                                for shop, coupons in shopwise_coupon.items()}   # sort from the largest to the smallest

    def get_shopwise_coupon_and_cost(self, prev: Optional[TreeNode], action: str) -> Tuple[Dict, Dict]:
        """
        An API for easily getting coupon and cost of each shop.

        :param prev: a tree node object representing the choice status (back to last commodity selected)
        :param action: current selected commodity

        :return: two dicts mapping shop names to the total got coupons and total costs respectively.
        """

        cost_by_shop = {shop: 0 for shop in self.shop_types}

        if prev is not None:
            for commodity in prev.history:
                cost_by_shop[self.shops[commodity]] += self.price[commodity]

        if action != '*STOP*':
            cost_by_shop[self.shops[action]] += self.price[action]

        coupon_by_shop = dict()
        for shop, total in cost_by_shop.items():
            for scheme in self.shopwise_coupon[shop]:
                if total >= scheme[1]:
                    coupon_by_shop[shop] = scheme[0]
                    break

        return coupon_by_shop, cost_by_shop


class SingleTmallD11Coupon(Discount):
    """
    This discount logic of Tmall's 11.11. Note that this class only consider one discount strategy.
    """

    def __init__(self, save: int, every: int, *args, **kwargs):
        """
        Instantiate an object representing the discount scheme of Tmall's 11.11.

        :param save: x from `save $x every $y`
        :param every: y from `save $x every $y`
        :param args: positional arguments passed to the parent class
        :param kwargs: keyword arguments passed to the parent class
        """

        super().__init__(*args, **kwargs)

        self.save = save
        self.every = every

    def __call__(self, prev: Optional[TreeNode], action: str) -> float:
        original_cost = 0

        if prev is not None:
            for commodity in prev.history:
                original_cost += self.price[commodity]

        original_cost += self.price[action] if action != '*STOP*' else 0

        return original_cost - (original_cost // self.every) * self.save


class MultiTmallD11Coupon(SchemewiseDiscount):
    """
    The discount logic considering multiple types of strategies.
    """

    def __call__(self, prev: Optional[TreeNode], action: str) -> float:
        coupon_by_scheme, cost_by_scheme = self.get_schemewise_coupon_and_cost(prev, action)

        return sum(cost_by_scheme.values()) - sum(coupon_by_scheme.values())


class ShopwiseMultiTmallD11Coupon(ShopwiseDiscount, SchemewiseDiscount):
    """
    The discount logic taking coupon of each shop into consideration.
    """

    def __call__(self, prev: Optional[TreeNode], action: str) -> float:
        coupon_by_scheme, cost_by_scheme = self.get_schemewise_coupon_and_cost(prev, action)
        coupon_by_shop, cost_by_shop = self.get_shopwise_coupon_and_cost(prev, action)

        return sum(cost_by_scheme.values()) - sum(coupon_by_scheme.values()) - sum(coupon_by_shop.values())
