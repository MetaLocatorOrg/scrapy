# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import json
import math
import re

from scrapy import Request
from scrapy.log import INFO, ERROR

from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider
from HP_Master_Project.utils import is_empty


class BhphotovideoSpider(BaseProductsSpider):
    name = 'bhphotovideo'
    allowed_domains = ['bhphotovideo.com']

    SEARCH_URL = "https://www.bhphotovideo.com/c/search?Ntt={search_term}&N=0&InitialSearch=yes&sts=ma&Top+Nav-Search="

    PAGINATE_URL = "https://www.bhphotovideo.com/c/search?sts=ma&N=0&pn={page}&Ntt={search_term}"

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    TOTAL_MATCHES = None

    RESULT_PER_PAGE = None

    def __init__(self, *args, **kwargs):
        super(BhphotovideoSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/60.0.3112.90 Safari/537.36"

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def parse_product(self, response):
        product = response.meta.get('product', ProductItem())

        # Parse name
        name = self._parse_name(response)
        product['name'] = name

        # Parse brand
        product['brand'] = self._parse_brand(response)

        # Parse image
        image = self._parse_image(response)
        product['image'] = image

        # Parse link
        link = response.url
        product['link'] = link

        # Parse model
        product['model'] = self._parse_model(response)

        # Parse upc
        product['upc'] = self._parse_upc(response)

        # Parse ean
        product['ean'] = None

        # Parse currencycode
        product['currencycode'] = 'USD'

        # Set locale
        product['locale'] = 'en-US'

        # Parse price
        product['price'] = self._parse_price(response)

        # Parse sale price
        product['saleprice'] = self._parse_sale_price(response)

        # Parse sku
        product['sku'] = self._parse_sku(response)

        # Parse retailer_key
        product['retailer_key'] = self._parse_retailer_key(response)

        # Parse in_store
        product['instore'] = self._parse_instore(response)

        # Parse productstockstatus
        product['productstockstatus'] = self._parse_stock_status(response)

        # Parse categories
        product['categories'] = self._parse_categories(response)

        # Parse gallery
        product['gallery'] = self._parse_gallery(response)

        # Parse features
        product['features'] = self._parse_features(response)

        # Parse condition
        product['condition'] = self._parse_condition(response)

        yield product

    @staticmethod
    def _parse_name(response):
        name = response.css('h1[data-selenium="productTitle"]::text').extract()
        if name:
            return name[0]
        return ''

    def _parse_brand(self, response):
        data = response.css('section.app-layout>div>script[type="application/ld+json"]::text').extract_first()
        if data:
            json_data = json.loads(data)
            return self.clear_text(json_data.get('brand', {}).get('name'))

    def _parse_sku(self, response):
        data = response.css('section.app-layout>div>script[type="application/ld+json"]::text').extract_first()
        if data:
            json_data = json.loads(data)
            return self.clear_text(json_data.get('sku'))

    @staticmethod
    def _parse_upc(response):
        upc = response.css('div[data-selenium="overviewUpcText"]::text').extract()
        if upc:
            return upc[0].replace('UPC:', '').strip()

    def _get_stock_request(self, response):
        html = response.text
        url = 'https://store.hp.com/us/en/HPServices?langId={}&storeId={}&catalogId={}&action=pis&catentryId={}&modelId='
        catentry_id = re.findall('data-a2c=\'{"itemId":"(\d+?)",', html) or re.findall(
            '"itemId":"(\d+)', html)
        if catentry_id:
            catentry_id = catentry_id[0]
        else:
            self.log("Cannot find catentry_id for %s" % response.url, INFO)
            return
        store_id = (re.findall('var storeId = \'(\d+?)\';', html) or re.findall('storeId=(\d+)', html))
        if store_id:
            store_id = store_id[0]
        else:
            self.log("Cannot find store_id for %s" % response.url, INFO)
            return
        lang_id = "-1"
        catalog_id = re.findall('var catalogId = \'(\d+?)\';', html) or re.findall('catalogId=(\d+)', html)
        if catalog_id:
            catalog_id = catalog_id[0]
        else:
            self.log("Cannot find catalog_id for %s" % response.url, INFO)
            return
        return url.format(lang_id, store_id, catalog_id, catentry_id)

    def _parse_stock_status(self, response):
        stock_text = response.css('span[data-selenium="stockStatus"]::text').extract()

        # default stock status
        stock_value = self.STOCK_STATUS['OUT_OF_STOCK']
        if stock_text:
            if stock_text[0].lower() == 'in stock':
                stock_value = self.STOCK_STATUS['IN_STOCK']

        return stock_value

    @staticmethod
    def _parse_categories(response):
        categories = response.css('a[data-selenium="linkCrumb"]::text').extract()
        if categories:
            categories.remove(u'Home')
            return categories

    def _parse_model(self, response):
        data = response.css('section.app-layout>div>script[type="application/ld+json"]::text').extract_first()
        if data:
            json_data = json.loads(data)
            return self.clear_text(json_data.get('mpn'))

    @staticmethod
    def _parse_image(response):
        img = response.css('img[data-selenium="inlineMediaMainImage"]::attr(src)').extract()
        return img

    @staticmethod
    def _parse_gallery(response):
        gallery = response.css('img[data-selenium="thumbnailImage"]::attr(src)').extract()
        return gallery

    @staticmethod
    def _parse_price(response):
        price = response.css('div[data-selenium="pricingPrice"]::text').extract()
        if price:
            return float(price[0].replace("$", "").replace(",", ""))

    @staticmethod
    def _parse_sale_price(response):
        sale_price = response.css('div[data-selenium="strikeThroughPrice"]::text').extract()
        if sale_price:
            return float(sale_price[0].replace("Price", "").replace("$", "").replace(",", "").strip())

    def _parse_retailer_key(self, response):
        retailer_key = re.findall('/product/(.*?)/', response.url)

        if retailer_key:
            return self.clear_text(retailer_key[0])

    def _parse_instore(self, response):
        if self._parse_price(response):
            return 1

        return 0

    def _parse_features(self, response):
        features = response.css('li[data-selenium="sellingPointsListItem"]::text').extract()
        return features

    def _parse_condition(self, response):
        # used
        used_label = response.css('div[data-selenium="usedLabel"]::text').extract()
        if used_label:
            if used_label[0] == 'Used':
                return 3

        # refurbished
        title = self._parse_name(response)
        if 'refurbished' in title.lower():
            return 2
        return 1

    def clear_text(self, str_result):
        return str_result.replace("\t", "").replace("\n", "").replace("\r", "").replace(u'\xa0', ' ').strip()

    def _scrape_total_matches(self, response):
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        # from javascript => "searchCount":   "N"
        totals = re.findall('searchCount"\s*:\s*"(\d+)?"', response.text)
        if totals:
            if totals[0].isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals[0])
                return int(totals[0])

        # top pagination => 1 - 24 of N
        total_matches_text = ' '.join(
            map(str.strip, response.css('span[data-selenium="paginationNumber"] ::text').extract()))
        totals = re.findall('of\s*(\d+)?', total_matches_text)
        if totals:
            if totals[0].isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals[0])
                return int(totals[0])

        # Bottom pagination => Page 1 of 10   |   1 - 24 of N Items
        total_matches_text = ' '.join(map(str.strip, response.css('p.pageNuber ::text').extract()))
        totals = re.findall('of\s*(\d+)?', total_matches_text)
        if totals:
            if totals[-1].isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals[-1])
                return int(totals[-1])

    def _scrape_results_per_page(self, response):
        if self.retailer_id:
            return None
        result_per_page = len(response.css('div[data-selenium="itemDetail"]').extract())
        if result_per_page:
            if not self.RESULT_PER_PAGE:
                self.RESULT_PER_PAGE = int(result_per_page)
            return int(result_per_page)

    def _scrape_product_links(self, response):
        link_list = []
        if self.retailer_id:
            data = json.loads(response.body)
            for link in data:
                link = link['product_link']
                link_list.append(link)
            for link in link_list:
                yield link, ProductItem()
        else:
            links = response.css(
                'div[data-selenium="itemDetail"] a[data-selenium="itemHeadingLink"]::attr(href)').extract()
            links = [response.urljoin(x) for x in links]
            for link in links:
                yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None

        search_term = response.meta['search_term']
        self.current_page += 1

        if self.current_page < math.ceil(self.TOTAL_MATCHES / 24.0):
            next_page = response.css('a[data-selenium="pn-next"]::attr(href)').extract()
            if next_page:
                return response.urljoin(next_page[0])

            next_page = self.PAGINATE_URL.format(search_term=search_term, page=self.current_page)
            return next_page
