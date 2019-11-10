"""
This file gives the criterion to evaluate a list of choices so that the MCT will get updated and most sensible strategy
will get proposed as well.
"""


from typing import *
import numpy as np

from algorithms.mcts import TreeNode
from .discount import Discount


class Reward:
    """
    The base class for all rewards defining basic API and fundamental logic.
    """

    def __init__(self, original_discount: Dict, want_score: Dict, price: Dict, budget: int, *args, **kwargs):
        """
        Instantiate a reward calculator recording information relevant to commodities.

        :param original_discount: the discount proposed w.r.t. each commodity, in currency (instead of percentage)
        :param want_score: a map from commodity to a subjective desiring score (1 ~ 5)
        :param price: a dict mapping from the name of commodities to their prices (haven't discounted respectively or
            couponed overall)
        :param budget: the overall budget
        :param args: not used positional argument making compatible among descendants
        :param kwargs: not used keyword argument making compatible among descendants
        """

        self.discount = original_discount
        self.want = want_score
        self.price = price
        self.budget = budget

    def __call__(self, node: Optional[TreeNode]) -> float:
        """
        The API to be called by a TreeNode object.

        :param node: the final node representing the entire shopping list

        :return: a float number from 0 to 1 representing reward. higher means better.
        """

        raise NotImplementedError

    def summarize(self, strategies: List[Tuple], calculator: Discount) -> List[Tuple]:
        """
        This method enriched the information given the strategies deduced by algorithms.

        :param strategies: a list of strategies. each item within the list should follow the format as:
            ([commodity_name], strategy_score)
        :param calculator: a discount calculator object to be called to acquire the total cost of the strategies

        :return: a list with each item of which conforms to as follows:
            ([commodity_name], strategy_score, summed_want_score, total_discount(in percentage), total_cost)
        """

        enriched = list()
        for strategy, score in strategies:
            cost = calculator.sum(strategy)

            want = 0
            original_price = 0

            for commodity in strategy:
                want += self.want[commodity]
                original_price += self.price[commodity]

            discount = 1 - (original_price - cost) / (original_price + 1e-4)

            enriched.append((strategy, score, want, discount, cost))

        return enriched


class MeanAveragedWant(Reward):
    """
    A reward considering total cost, total discount and total want.

    The want scores are first weighted averaged by the corresponding discount, and then the result is square-meaned with
    the term of normalized budget remain. i.e.

    reward = √[( [(∑ discount × want) ÷ ∑ discount]^2 + [(budget - total_cost) ÷ budget]^2 ) ÷ 2]

    for further adapting, a hyperparameter λ to leverage the impact of total cost (balance between frugality and
    enjoyment) as:

    reward = √[( [(∑ discount × want) ÷ ∑ discount]^2 + λ × [(budget - total_cost) ÷ budget]^2 ) ÷ (1 + λ)]
    """

    def __init__(self, lambd: float, count: Dict, *args, **kwargs):
        """
        Instantiate the reward acquiring logic introduced above.

        :param lambd: the hyperparameter representing the relevant importance of budget remaining. higher means more
            important.
        :param count: the number to bought of each commodity in the shopping cart
        :param args: positional arguments passed to the parent class
        :param kwargs: keyword arguments passed to the parent class
        """

        super().__init__(*args, **kwargs)
        self.lambd = lambd
        assert lambd >= 0

        self.max_want = np.max(np.array(list(self.want.values())))

        total_price = 0
        for commodity in count:
            if commodity != '*STOP*':
                total_price += count[commodity] * (self.price[commodity] - self.discount[commodity])

        self.avg_price = total_price / sum(count.values())

    def __call__(self, node: Optional[TreeNode]) -> float:
        if node is None:
            return 0

        remain = self.budget - node.v
        if remain < 0:
            return 0

        # prepare necessary data
        choices = node.history

        want = np.array([self.want[choice] for choice in choices])
        want = want / self.max_want
        original_discount = np.array([self.discount[choice] for choice in choices])

        original_price = sum([self.price[choice] for choice in choices])
        coupon_discount = original_price - (self.budget - remain)

        final_discount = original_discount + coupon_discount * original_discount / original_discount.sum()

        # calculate the AW
        aw = (want * final_discount / final_discount.sum()).sum()

        # normalize remain
        remain /= self.budget
        remain *= (self.budget - remain) / self.avg_price

        return float(np.sqrt((aw**2 + self.lambd * remain**2) / (1 + self.lambd)))


class MeanReverseAveragedDiscount(MeanAveragedWant):
    """
    A reward considering total cost, total discount and total want. This reward is the advance of MAW, solving the
    problem that only the most wanted commodity will be chosen.

    The discount ratio is first weighted averaged by reverse want (5 by default - want), and then the result is
    square-meaned with the term of normalized budget remain. i.e.

    reward = √[( [(∑ discount × reverse_want) ÷ ∑ reverse_want]^2 + [(budget - total_cost) ÷ budget]^2 ) ÷ 2]

    for further adapting, a hyperparameter λ to leverage the impact of total cost (balance between frugality and
    enjoyment) as:

    reward = √[( [(∑ discount × reverse_want) ÷ ∑ reverse_want]^2 + λ × [(budget - total_cost) ÷ budget]^2 ) ÷ (1 + λ)]
    """

    def __call__(self, node: Optional[TreeNode]) -> float:
        if node is None:
            return 0

        remain = self.budget - node.v
        if remain < 0:
            return 0

        # prepare necessary data
        choices = node.history

        want = np.array([self.want[choice] for choice in choices])
        reverse_want = 1 - want / self.max_want

        original_discount = np.array([self.discount[choice] for choice in choices])
        original_price = np.array([self.price[choice] for choice in choices])

        original_total = sum([self.price[choice] for choice in choices])
        coupon_discount = original_total - (self.budget - remain)

        final_discount = original_discount + coupon_discount * original_discount / original_discount.sum()
        final_discount = final_discount / original_price

        # calculate the RAD
        rad = (reverse_want * final_discount / (reverse_want.sum() + 1e-4)).sum()

        # normalize remain
        remain /= self.budget
        remain *= (self.budget - remain) / self.avg_price

        return float(np.sqrt((rad**2 + self.lambd * remain**2) / (1 + self.lambd)))


class MeanAveragedHarmony(MeanAveragedWant):
    """
    A reward considering total cost, total discount and total want.
    This reward combines the two rewards mentioned above to avoid the model to output either most want strategies or
    most discounted strategies

    The want scores are first weighted by the corresponding discount but normalized by both want and discount, and then
    the result is square-meaned with the term of normalized budget remain. i.e.

    reward = √[( [(∑ discount × want) ÷ ∑ (discount + want)]^2 + [(budget - total_cost) ÷ budget]^2 ) ÷ 2]

    for further adapting, a hyperparameter λ to leverage the impact of total cost (balance between frugality and
    enjoyment) as:

    reward = √[( [(∑ discount' × want) ÷ ∑ (discount' + want)]^2 + λ × [(budget - total_cost) ÷ budget]^2 ) ÷ (1 + λ)]

    also here, the discount is normalized by its max value respectively to reduce the intrinsic difference of
    impact.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        discount = np.array(list(self.discount.values()))
        price = np.array(list(self.price.values()))

        self.max_discount = np.max(discount / price)

    def __call__(self, node: Optional[TreeNode]) -> float:
        if node is None:
            return 0

        remain = self.budget - node.v
        if remain < 0:
            return 0

        # prepare necessary data
        choices = node.history

        want = np.array([self.want[choice] for choice in choices])
        want = want / self.max_want
        original_discount = np.array([self.discount[choice] for choice in choices])

        original_price = np.array([self.price[choice] for choice in choices])
        coupon_discount = np.sum(original_price) - (self.budget - remain)

        final_discount = original_discount + coupon_discount * original_discount / original_discount.sum()
        final_discount = final_discount / original_price / self.max_discount

        # calculate the AH
        ah = (want * final_discount / (want + final_discount)).sum()

        # normalize remain
        remain /= self.budget
        remain *= (self.budget - remain) / self.avg_price

        return float(np.sqrt((ah**2 + self.lambd * remain**2) / (1 + self.lambd)))


class MeanAveragedOverallHarmony(MeanAveragedWant):
    """
    A reward considering total cost, total discount and total want.
    Instead of considering the commodity-wise harmonic average, this class consider the harmonic average after the
    whole strategy is analyzed, i.e.

    reward = √[( [(∑ discount × ∑ want) ÷  (∑ discount + ∑ want)]^2 + [(budget - total_cost) ÷ budget]^2 ) ÷ 2]

    for further adapting, a hyperparameter λ to leverage the impact of total cost (balance between frugality and
    enjoyment) as:

    reward = √[( [(∑ discount' × ∑ want) ÷ (∑ discount' + ∑ want)]^2 + λ × [(budget - total_cost) ÷ budget]^2 ) ÷ (1 + λ)]

    also here, the discount is normalized by its max value respectively to reduce the intrinsic difference of
    impact.
    """

    def __call__(self, node: Optional[TreeNode]) -> float:
        if node is None:
            return 0

        remain = self.budget - node.v
        if remain < 0:
            return 0

        # prepare necessary data
        choices = node.history

        want = np.array([self.want[choice] for choice in choices])
        want = want / self.max_want

        original_discount = np.array([self.discount[choice] for choice in choices])

        original_price = np.array([self.price[choice] for choice in choices])
        coupon_discount = np.sum(original_price) - (self.budget - remain)

        total_price = np.sum(original_price)
        price_list = np.array(list(self.price.values()))
        equivalent_num = total_price / price_list
        equivalent_discount = np.array(list(self.discount.values())) + coupon_discount / (equivalent_num + 1e-4)
        equivalent_discount = equivalent_discount / price_list

        max_discount = np.max(equivalent_discount)

        final_discount = original_discount + coupon_discount * original_discount / original_discount.sum()
        final_discount = final_discount / original_price / max_discount

        # calculate the AOH
        aoh = np.sum(want) * np.sum(final_discount) / (np.sum(want) + np.sum(final_discount) + 1e-4)

        # normalize remain
        remain /= self.budget
        remain *= (self.budget - remain) / self.avg_price

        return float(np.sqrt((aoh**2 + self.lambd * remain**2) / (1 + self.lambd)))
