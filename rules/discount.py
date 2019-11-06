"""
This file indicates the rules of e-commercial discounts by rewrite relevant method of MCTS nodes.
"""


from typing import *
from algorithms.mcts import TreeNode


class Discount:
    """
    This class defines the discount rule and reserve a __call__ API.
    """

    def __init__(self, price: Dict, modifier: Optional[Callable[[Dict, List], Dict]] = None):
        """
        Instantiate an object recording the commercials' price info.

        :param price: a dict mapping from the name of commercials to their prices.
        :param modifier: a function taking original prices and bought commercials as input and update the price info.
        """

        self.price = price
        self.modifier = modifier

    def __call__(self, prev: Optional[TreeNode], action: str) -> float:
        """
        The API to be called by the TreeNode object.

        :param prev: the parent node of current considered node.
        :param action: the commercial bought of current node.

        :return: discounted total price up now.
        """

        raise NotImplementedError


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
            for commercial in prev.history:
                original_cost += self.price[commercial]

        original_cost += self.price[action] if action != '*STOP*' else 0

        return original_cost - (original_cost // self.every) * self.save


class MultiTmallD11Coupon(Discount):
    """
    The discount logic considering multiple types of strategies.
    """

    def __init__(self, scheme_of_commercials: Dict, *args, **kwargs):
        """
        Instantiate an object representing multiple discount logics simultaneously of Tmall's 11.11.

        :param scheme_of_commercials: a mapping from commercials' name to its discount scheme (represented as tuple
            (save, every)).
        :param args: positional arguments passed to the parent class
        :param kwargs: keyword arguments passed to the parent class
        """

        super().__init__(*args, **kwargs)

        self.schemes = scheme_of_commercials
        self.scheme_types = set(self.schemes.values())

    def __call__(self, prev: Optional[TreeNode], action: str) -> float:
        cost_by_scheme = {scheme_type: 0 for scheme_type in self.scheme_types}

        if prev is not None:
            for commercial in prev.history:
                cost_by_scheme[self.schemes[commercial]] += self.price[commercial]

        if action != '*STOP*':
            cost_by_scheme[self.schemes[action]] += self.price[action]

        discounted = 0
        for scheme_type, total in cost_by_scheme.items():
            discounted += total - (total // scheme_type[1]) * scheme_type[0]

        return discounted
