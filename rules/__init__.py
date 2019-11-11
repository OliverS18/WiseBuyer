"""
This package defines the overall discount rule and universal evaluation functions.
"""


from . import discount
from . import crit


coupon = {'tmall': discount.ShopwiseMultiTmallD11Coupon}
score = {'maw': crit.MeanAveragedWant,
         'mrad': crit.MeanReverseAveragedDiscount,
         'mah': crit.MeanAveragedHarmony,
         'moha': crit.MeanOverallHarmonicAverage,
         'amoha': crit.AdvancedMeanOverallHarmonicAverage}
