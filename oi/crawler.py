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
import tqdm
import re
import time
from typing import *
import requests
import cv2

from .config import cfg
from .interact.inline_display import img2terminal, clear


class TaobaoBrowser:
    """
    The overall structure warping the crawl logic all together.
    """

    def __init__(self, target_time: Optional[time.struct_time] = None):
        """
        Instantiate a TaobaoBrowser object.

        :param target_time: the target time to perform purchase action. may infect availability of coupons.
            If provided, it should be converted from the format as `yyyy.mm.dd`
        """

        # avoid recognized by anti-crawler mechanism
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 1})
        options.add_argument('disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')

        # set up browser
        self.browser = webdriver.Chrome(executable_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     'chromedriver'),
                                        options=options)
        self.browser.minimize_window()

        self.wait = WebDriverWait(self.browser, 60)
        self.schedule_time = target_time

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
        print('\n\033[0mLoading login interface...\033[0m')
        self.browser.get(url)
        self.browser.implicitly_wait(3)            # wait til the page is fully loaded

        # place at proper position
        self.browser.set_window_size(350, 500)
        self.browser.execute_script('let where = document.getElementById("J_LoginBox").getBoundingClientRect(); '
                                    'let doc = document.documentElement; '
                                    'doc.scrollTop += where.top - 50; doc.scrollLeft += where.left - 50;')

        # switch to QR code login mode
        if self._exist('#content .content-layout .module-static'):
            element = self.browser.find_element_by_css_selector('#J_Static2Quick')
            self.browser.execute_script("arguments[0].click();", element)

        print('\n\033[32mLogin interface simulated successfully.\033[0m')

        qr_code = self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,
                                                                  '#J_QRCodeImg img'))).get_attribute('src')
        qr_img = requests.get(qr_code).content

        with open(os.path.join(cfg.io.temp_path, cfg.io.qr), 'wb') as img:
            img.write(qr_img)

        print('\n\033[34mPlease scan the QR code to login.\033[0m')
        print('\n\033[33mPlease rest assured. '
              '\nYour account authentication will \033[1;33mnot\033[0;33m be preserved and will be used '
              '\033[33;1monly\033[0;33m to acquire necessary cart information.\033[0m\n')

        height = img2terminal(cv2.imread(os.path.join(cfg.io.temp_path, cfg.io.qr)), width=48, indent=1)

        # wait until acquiring member's nick name representing successfully logined
        _ = self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,
                                                            '.site-nav-bd '
                                                            '> ul.site-nav-bd-l '
                                                            '> li#J_SiteNavLogin '
                                                            '> div.site-nav-menu-hd '
                                                            '> div.site-nav-user '
                                                            '> a.site-nav-login-info-nick')))

        clear(height)
        print('\033[32mSuccessfully logged in.\033[0m')

    def crawl(self, name_length: Optional[int] = None) -> Tuple[Dict, Dict]:
        """
        Parse commodity information in the cart.

        :param name_length: the maximize length of the commodities name. Name longer than this value will be truncated.
            None indicates never truncating.

        :return: two dicts representing commodity information and shopwise coupon schemes respectively required by the
            main service.py
        """
        # enter the page of cart
        self.browser.maximize_window()
        self.browser.set_window_position(-10000, 10000)

        print('\n\033[0mAcquiring cart information...\033[0m\n')

        self.browser.get("https://cart.taobao.com/cart.htm")

        # scroll down to get all the goods in cart shown
        self._swipe()

        # acquire source code of current page
        html = self.browser.page_source
        doc = pq.PyQuery(html)

        # acquire all orders with respect to shops
        shops = doc('.J_Order')

        # reserve container
        shop_coupons = dict()
        commodities = dict()

        # iterate over shops
        with tqdm.tqdm(dynamic_ncols=True, desc='Shops', total=shops.length,
                       bar_format='\033[1;7;32m{desc} \033[0;7;32m{n_fmt}\033[1;7;32m/\033[0;7;32m{total_fmt}\033[0m '
                                  '|{bar}| '
                                  '\033[1;32m{percentage:3.0f}\033[0;32m%\033[0m '
                                  '\033[1m[\033[32m{elapsed}\033[0m elapsed, '
                                  '\033[1;32m{remaining}\033[0m remain\033[1m]\033[0m') as bar:
            for shop in shops.items():
                bar.update()

                # parse shop name
                shop_name = shop.find('.shop-info>a').text()

                if shop_name == '天猫超市':
                    continue                    # TODO: cannot handle 天猫超市, since its discount scheme varies too much

                css_id = shop.attr('id')        # save for following click operation

                # try if there are shop coupons
                if shop.find('.J_MyShopCoupon'):
                    available_coupons = list()

                    self.browser.execute_script('arguments[0].click();',
                                                self.browser.find_element_by_css_selector('#{} .J_MyShopCoupon em'
                                                                                          .format(css_id)))
                    _ = self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,
                                                                        '.coupon-popup .coupon-list ')))
                    doc = pq.PyQuery(self.browser.page_source)
                    coupon_list = doc('.coupon-popup').find('li.coupon').items()

                    for coupon in coupon_list:
                        scheme = re.match('.*?' + self._translate('满') + '(\\d+)' + self._translate('减') + '(\\d+).*?',
                                          coupon.find('.coupon-title').text())
                        if scheme:
                            scheme = scheme.groups()
                        else:
                            after = re.match('.*?' + self._translate('满') + '(\\d+\\.\\d*).*',
                                             coupon.find('.coupon-title').text()).group(1)
                            save = coupon.find('.coupon-amount').text().strip('¥ ')

                            scheme = (after, save)

                        save_after_ = (int(scheme[1]), float(scheme[0]))

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

                    if scheme.find('.bundle-hd .bd-content'):
                        matched = \
                            re.match('.*?' + self._translate('满') + '(\\d+)' + self._translate('减') + '(\\d+).*?',
                                     scheme.find('.bundle-hd .bd-content').text())
                        if matched:
                            good_scheme = (int(matched.group(2)), int(matched.group(1)))

                    goods = scheme.find('.item-content').items()
                    for good in goods:
                        if good.find('.td-chk').text() == '失效':
                            continue

                        good_name = good.find('.item-info a.J_GoldReport').attr('title')
                        if name_length and len(good_name) > name_length:
                            good_name = good_name[:name_length] + '... '

                        # good_pic = good.find('.item-pic img').attr('src')

                        good_prop = str()
                        props = good.find('.item-props .sku-line').items()
                        for prop in props:
                            good_prop += re.match('.*?' + self._translate('：') + '(.*)', prop.text()).group(1)
                            good_prop += ', '

                        good_prop = good_prop.strip(', ')

                        good_price = float(good.find('.price-now').text().strip('￥'))
                        good_amount = int(good.find('.item-amount input').attr('data-now')) \
                            if good.find('.item-amount input') else int(good.find('.item-amount').text())   # if fixed

                        # TODO: How to get future price?
                        good_discounted_price = good_price
                        if good.find('.item-info>.item-other-info>.promo-logos>.promo-logo'):
                            base_page = self.browser.current_window_handle

                            good_link = good.find('.item-info a.J_GoldReport').attr('href')
                            self.browser.execute_script("window.open('https:" + good_link + "');")
                            self.browser.switch_to.window(self.browser.window_handles[-1])

                            for prop in self.browser.find_elements_by_css_selector('.tb-key dd a'):
                                if prop.get_attribute('textContent').strip() in good_prop.split(', '):
                                    self.browser.execute_script("arguments[0].click();", prop)

                            good_discounted_price \
                                = float(self.browser.find_element_by_css_selector('#J_ActivityPrice span').text)

                            self.browser.close()
                            self.browser.switch_to.window(base_page)

                        if good_prop:
                            good_prop = ': ' + good_prop

                        commodities[good_name + good_prop] = (good_price,
                                                              good_discounted_price,
                                                              good_amount,
                                                              good_scheme,
                                                              shop_name)

        print('\n\033[32mCart information acquired successfully.\033[0m')

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
