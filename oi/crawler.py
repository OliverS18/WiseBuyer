"""
This file implements the crawler for parsing information from Taobao's cart page.

The crawler here is implemented based on shengqiangzhang's script
(https://github.com/shengqiangzhang/examples-of-web-crawlers/blob/master/3.淘宝已买到的宝贝数据爬虫(已模拟登录)/taobao_buy_crawler.py)
and Andy、Tao's implementation
(https://blog.csdn.net/tao15716645708/article/details/98870266)
Much thanks to the authors.
"""


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as ec
import pyquery as pq

import os
import re
import time
from typing import *


class TaobaoBrowser:
    """
    The overall structure warping the crawl logic all together.
    """

    def __init__(self, target_time: Optional[str] = None):
        """
        Instantiate a TaobaoBrowser object.

        :param target_time: the target time to perform purchase action. may infect availability of coupons.
            If provided, it should conforms to the format as `yyyy.mm.dd`
        """

        # avoid recognized by anti-crawler mechanism
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 1})
        options.add_argument('disable-infobars')
        options.add_argument('--no-sandbox')

        # set up browser
        self.browser = webdriver.Chrome(executable_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     'chromedriver'),
                                        options=options)
        self.browser.minimize_window()

        self.wait = WebDriverWait(self.browser, 60)
        self.schedule_time = time.strptime(target_time, '%Y.%m.%d') if target_time else None

        self.login()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.quit()

    def login(self, url: str = 'https://login.taobao.com/member/login.jhtml') -> NoReturn:
        """
        Since taobao.com requires login first to obtain cart information, this function warps the login procedure and
        enables the browser to enter the cart page.

        :param url: The page of login. Default value is usually correct.
        """
        # open the url
        self.browser.get(url)
        self.browser.implicitly_wait(3)            # wait til the page is fully loaded

        # place at proper position
        self.browser.set_window_size(350, 500)
        self.browser.execute_script('let where = document.getElementById("J_LoginBox").getBoundingClientRect(); '
                                    'let doc = document.documentElement; '
                                    'doc.scrollTop += where.top - 50; doc.scrollLeft += where.left - 50;')

        # switch to QR code login mode
        if self._exist('#content .content-layout .module-static'):
            self.browser.find_element_by_css_selector('#J_Static2Quick').click()

        # wait until acquiring member's nick name representing successfully logined
        _ = self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,
                                                            '.site-nav-bd '
                                                            '> ul.site-nav-bd-l '
                                                            '> li#J_SiteNavLogin '
                                                            '> div.site-nav-menu-hd '
                                                            '> div.site-nav-user '
                                                            '> a.site-nav-login-info-nick')))

    def crawl(self, name_length: Optional[int] = None) -> Tuple[Dict, Dict]:
        """
        Parse commodity information in the cart.

        :param name_length: the maximize length of the commodities name. Name longer than this value will be truncated.
            None indicates never truncating.

        :return: two dicts representing commodity information and shopwise coupon schemes respectively required by the
            main service.py
        """
        # TODO: make this process silent in background
        # enter the page of cart
        self.browser.maximize_window()
        self.browser.set_window_position(-10000, 10000)
        self.browser.get("https://cart.taobao.com/cart.htm")

        # scroll down to get all the goods in cart shown
        self._swipe()

        # acquire source code of current page
        html = self.browser.page_source
        doc = pq.PyQuery(html)

        # acquire all orders with respect to shops
        shops = doc('.J_Order').items()

        # reserve container
        shop_coupons = dict()
        commodities = dict()

        # iterate over shops
        for shop in shops:
            # parse shop name
            shop_name = shop.find('.shop-info .ww-small').attr('data-nick')

            if shop_name == '天猫超市':
                continue                        # TODO: cannot handle 天猫超市, since its discount scheme varies too much

            css_id = shop.attr('id')            # save for following click operation

            # try if there are shop coupons
            if shop.find('.J_MyShopCoupon'):
                available_coupons = list()

                self.browser.execute_script('arguments[0].click();',
                                            self.browser.find_element_by_css_selector('#{} .J_MyShopCoupon em'
                                                                                      .format(css_id)))
                _ = self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,
                                                                    '.coupon-popup .coupon-list ')))
                doc = pq.PyQuery(self.browser.page_source)
                coupon_list = doc('.coupon-popup').find('.coupon-info').items()

                for coupon in coupon_list:
                    scheme = re.match('.*?' + self._translate('满') + '(\\d+)' + self._translate('减') + '(\\d+).*?',
                                      coupon.find('.coupon-title').text()).groups()
                    save_after_ = (int(scheme[1]), int(scheme[0]))

                    valid_range = re.match('(.*)?-(.*)', coupon.find('.coupon-time').text()).groups()
                    valid_range = [time.strptime(timespot, '%Y.%m.%d') for timespot in valid_range]

                    if self.schedule_time is None or valid_range[0] <= self.schedule_time <= valid_range[1]:
                        available_coupons.append(save_after_)

                shop_coupons[shop_name] = available_coupons
            else:
                shop_coupons[shop_name] = [(0, 1)]

            # gather commodities of each discount scheme
            # TODO: currently cannot handle postage

            schemes = shop.find('.bundle').items()
            for scheme in schemes:
                good_scheme = (0, 1)

                if scheme.find('.bundle-hd'):
                    # TODO: check if the discount scheme is indeed displayed within such element
                    matched = re.match('.*?' + self._translate('每') + '(\\d+)' + self._translate('减') + '(\\d+).*?',
                                       scheme.find('.bundle-hd .bd-title').text())
                    if matched:
                        good_scheme = (int(matched.group(2)), int(matched.group(1)))

                goods = scheme.find('.item-content').items()
                for good in goods:
                    if good.find('.td-chk').text() == '失效':
                        continue

                    good_name = good.find('.item-info a.J_GoldReport').attr('title')
                    if name_length and len(good_name) > name_length:
                        good_name = good_name[:name_length] + '... '

                    good_pic = good.find('.item-pic img').attr('src')

                    good_prop = str()
                    props = good.find('.item-props .sku-line').items()
                    for prop in props:
                        good_prop += re.match('.*?' + self._translate('：') + '(.*)', prop.text()).group(1)
                        good_prop += ', '

                    good_prop = good_prop.strip(', ')

                    if good_prop:
                        good_prop = ': ' + good_prop

                    good_price = float(good.find('.price-now').text().strip('￥'))
                    good_amount = int(good.find('.item-amount input').attr('data-now')) \
                        if good.find('.item-amount input') else int(good.find('.item-amount').text())   # if fixed

                    # TODO: How to get future price?
                    good_discounted_price = good_price

                    commodities[good_name + good_prop] = (good_price,
                                                          good_discounted_price,
                                                          good_amount,
                                                          good_scheme,
                                                          shop_name)

        return commodities, shop_coupons

    def _swipe(self, interval: int = 1, safe: bool = False) -> NoReturn:
        while self.browser.execute_script("let doc = document.documentElement; "
                                          "return doc.scrollTop + doc.clientHeight < doc.scrollHeight;"):
            self.browser.execute_script("let doc = document.documentElement; "
                                        "doc.scrollTop = doc.scrollHeight;")

            time.sleep(interval * 2 / 3)

            if safe:
                # pretend mankind operation to avoid anti-crawler mechanism
                position = self.browser.execute_script("let doc = document.documentElement; return doc.scrollTop;")
                self.browser.execute_script("let doc = document.documentElement; doc.scrollTop = arguments[0] / 3;",
                                            position)
                time.sleep(interval / 3)
                self.browser.execute_script("let doc = document.documentElement; doc.scrollTop = arguments[0];",
                                            position)
            else:
                time.sleep(interval / 3)

    def _exist(self, selector: str) -> bool:
        try:
            self.browser.implicitly_wait(0.1)
            self.browser.find_element_by_css_selector(selector)
            self.browser.implicitly_wait(3)
            return True
        except NoSuchElementException:
            self.browser.implicitly_wait(3)
            return False

    @staticmethod
    def _translate(char: str) -> str:
        return char.encode('unicode-escape').decode('latin-1')


if __name__ == '__main__':
    # for debug
    with TaobaoBrowser() as bro:
        stuff = bro.crawl()

    for item in stuff:
        print(item)
