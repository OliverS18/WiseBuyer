"""
This package defines the overall discount rule and universal evaluation functions.
"""


from . import discount
from . import crit


coupon = {'tmall': discount.MultiTmallD11Coupon}
score = {'maw': crit.MeanAveragedWant}
