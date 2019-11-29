"""
This File parses arguments passed to the main script
"""


import argparse
import re as _re
from gettext import gettext as _

from ..logo import logo


class Formatter(argparse.MetavarTypeHelpFormatter):
    def add_logo(self, logo):
        self._add_item(lambda string: string, [logo])


class Parser(argparse.ArgumentParser):
    def format_help(self):
        formatter = self._get_formatter()

        # add logo
        formatter.add_logo('\n' + logo + '\n')

        # add description first
        formatter.add_text(self.description)

        # then usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()


def get_options() -> argparse.Namespace:
    """
    Parse argument from command line.

    :return: parsed option namespace.
    """
    parser = Parser(prog='WiseBuyer',
                    description='An assistant aiding you to make more sensible choices on Taobao.com '
                                'with more discount within limited budget.',
                    formatter_class=Formatter)

    parser.add_argument('-l', '--use_local',
                        action='store_true',
                        help='To use the previous cached json file instead of crawling it again from Taobao.')
    parser.add_argument('-b', '--budget',
                        type=float,
                        help='The budget in CNY.')
    parser.add_argument('-f', '--frugality',
                        type=float,
                        help='If the proposed choices is considered to be better if costint less, then this '
                             'coefficient is supposed to be set as a positive number. Larger means you caring more '
                             'about cost over the discount/desiring.')
    parser.add_argument('-d', '--display_num',
                        type=int,
                        help='Number of proposed choices you would like the program to demonstrate.')
    parser.add_argument('-e', '--elaborate',
                        type=int,
                        help='Since the program uses Monte Carlo Tree Search algorithm to search for choices, more '
                             'calculations will bring about solutions more sensible, but also more time consuming. '
                             'This argument controls the trade-off balance, where larger means more calculations. '
                             'Empirically, setting within 10 ~ 10000 works fine.')
    parser.add_argument('-c', '--confirm',
                        action='store_true',
                        help='Set if you want to make no edition on the json configuration and skip the confirm '
                             'procedure.')

    options = parser.parse_args()

    if options.budget and options.budget < 0:
        parser.error('Budget is not allowed to be lower than 0.')

    if options.frugality and options.frugality < 0:
        parser.error('Frugality coefficient is not allowed to be lower than 0.')

    if options.display_num and options.display_num <= 0:
        parser.error('Number of displayed choices is supposed to be greater than 0.')

    if options.elaborate and not 10 <= options.elaborate <= 10000:
        parser.error('Elaborate coefficient is supposed to be within 10 to 10000.')

    return options


arguments = get_options()
