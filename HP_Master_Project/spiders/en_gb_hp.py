# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

from scrapy.log import WARNING
from scrapy import Request
import re
import json
import math

from HP_Master_Project.utils import is_empty
from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider
from HP_Master_Project.extract_brand import extract_brand_from_first_words


class EnGbHpSpider(BaseProductsSpider):
    name = 'en_gb_hp'
    allowed_domains = ['store.hp.com', 'www.hp.com']

    SEARCH_URL = "http://eu1-search.doofinder.com/5/search?hashid=68255af0073c20fc7a549d26435bccd8&page=1&query={search_term}&rpp=5&type=CG953"
    PAGINATE_URL = "http://eu1-search.doofinder.com/5/search?hashid=68255af0073c20fc7a549d26435bccd8&page={page_no}&query={search_term}&rpp=5&type=CG953"
    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    total_matches = None

    headers = {'Origin': "http://store.hp.com"}

    def __init__(self, *args, **kwargs):
        super(EnGbHpSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/60.0.3112.90 Safari/537.36"

    def _parse_single_product(self, response):
        return self.parse_product(response)

    def parse_product(self, response):
        product = response.meta['product']
        if response.meta['req_url'] != response.url:
            if response.meta['req_url'].replace('http', 'https', 1) != response.url:
                return
        # Parse name
        name = self._parse_name(response)
        product['name'] = name

        # Parse image
        image = self._parse_image(response)
        product['image'] = image

        model = self._parse_model(response)
        product['model'] = model
        product['ean'] = None
        #
        product['currencycode'] = 'GBP'
        product['locale'] = 'en-UK'
        sku = self._parse_sku(response)
        product['sku'] = sku
        price = self._parse_price(response)
        product['price'] = price
        product['saleprice'] = price
        retailer_key = self._parse_retailer_key(response)
        product['retailer_key'] = retailer_key
        in_store = self._parse_instore(response)
        product['instore'] = in_store
        product['gallery'] = self._parse_gallery(response)
        features = self._parse_features(response)
        product['features'] = features
        product['condition'] = 1
        product['productstockstatus'] = self._parse_stock_status(response)
        self._parse_categories(response)
        return product

    @staticmethod
    def _parse_name(response):
        title = response.xpath('//h1[@class="pb-product__name"]/text()').extract()
        if title:
            return title[0]

    @staticmethod
    def _parse_image(response):
        img = response.xpath('//ul[@class="gal-nav"]/li/a/img/@data-src').extract()
        if img:
            return img[0]

    @staticmethod
    def _parse_sku(response):
        sku = response.xpath('//*[@itemprop="sku"]/@content')[0].extract()
        return sku

    def _parse_stock_status(self, response):
        stock_value = self.STOCK_STATUS['CALL_FOR_AVAILABILITY']
        try:
            stock_message = response.xpath('//*[@itemprop="availability"]/@content')[0].extract()
            if 'instock' in stock_message.lower():
                stock_value = self.STOCK_STATUS['CALL_FOR_AVAILABILITY']
            elif 'outofstock' in stock_message.lower():
                stock_value = self.STOCK_STATUS['OUT_OF_STOCK']
            elif 'callforavailability' in stock_message.lower():
                stock_value = self.STOCK_STATUS['CALL_FOR_AVAILABILITY']
            elif 'discontinued' in stock_message.lower():
                stock_value = self.STOCK_STATUS['OTHER']

        except BaseException as e:
            self.log("Error parsing stock status data: {}".format(e), WARNING)

        return stock_value

    @staticmethod
    def _parse_categories(response):
        product = response.meta['product']

        categories = response.xpath('//ul[contains(@class, "breadcrumbs")]/li/a/text()').extract()
        product['categories'] = categories
        return product

    def _parse_model(self, response):
        model = response.xpath('//p[contains(@class, "prod-nr")]/text()').extract()
        if model:
            return self.clear_text(model[0])

    @staticmethod
    def _parse_gallery(response):
        gallery = response.xpath('//ul[@class="gal-nav"]/li/a/img/@data-src').extract()
        return gallery

    @staticmethod
    def _parse_price(response):
        price = response.xpath('//*[@itemprop="price"]/@content')[0].extract()
        if price:
            return price

    def _parse_retailer_key(self, response):
        retailer_key = response.xpath('//div[@class="prodSku"]/span[@class="prodNum"]/text()').extract()
        if retailer_key:
            return self.clear_text(retailer_key[0])

    def _parse_instore(self, response):
        if self._parse_price(response):
            return 1

        return 0

    def _parse_shiptostore(self, response):
        if self._parse_shippingphrase(response):
            return 1

        return 0

    def _parse_shippingphrase(self, response):
        pharse = response.xpath('//div[@class="estShipMessagePDP"]/text()').extract()
        if pharse:
            return self.clear_text(pharse[0])

    def _parse_features(self, response):
        features = []
        features_name = response.xpath('//div[contains(@class, "specs__table")]/table[@class="specs-table"]/tr')
        for f_name in features_name:
            key = f_name.xpath('.//th/text()').extract()
            value = f_name.xpath('.//td/text()').extract()
            if value:
                features.append({key[0]: value[0]})
        return features

    def clear_text(self, str_result):
        return str_result.replace("\t", "").replace("\n", "").replace("\r", "").replace(u'\xa0', ' ').strip()

    def _scrape_total_matches(self, response):
        data = json.loads(response.body)
        if self.retailer_id:
            return len(data)
        self.total_matches = data['total']
        return self.total_matches

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
            data = json.loads(response.body)
            self.total_matches = data['total']
            links = []
            for result in data['results']:
                links.append(result['link'])

            for link in links:
                yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return None
        search_term = response.meta['search_term']
        self.current_page += 1
        if self.current_page < math.ceil(self.total_matches / 5.0):
            next_page = self.PAGINATE_URL.format(search_term=search_term, page_no=self.current_page)
            return next_page
