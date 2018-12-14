# - * - coding: utf-8 -*-#
from __future__ import absolute_import, division, unicode_literals

import json
import math
import re

import requests

from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider, FormatterWithDefaults


class CurrysSpider(BaseProductsSpider):
    name = "en-GB_Currys"
    allowed_domains = ['currys.co.uk', 'www.currys.co.uk']

    SEARCH_URL = "https://www.currys.co.uk/gbuk/search-keywords/xx_xx_xx_xx_xx/{search_term}/{page_num}_50/" \
                 "relevance-desc/xx-criteria.html"

    API_URL = \
        'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
        '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
        '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    TOTAL_MATCHES = None

    def __init__(self, *args, **kwargs):
        super(CurrysSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/60.0.3112.90 Safari/537.36"
        self.url_formatter = FormatterWithDefaults(page_num=1)

    def start_requests(self):
        # print "Start Requests Called"
        for request in super(CurrysSpider, self).start_requests():
            if not self.product_url:
                request = request.replace(callback=self.parse_search, dont_filter=True)
            yield request

    def parse_search(self, response):
        # print "Parse Search Called"
        page_title = response.xpath('//div[@class="col12 resultList"]').extract()
        if page_title or self.retailer_id:
            return self.parse(response)
        else:
            return self._parse_single_product(response)

    def _parse_single_product(self, response):
        # print "Parse Single Product Called"
        return self.parse_product(response)

    def parse_product(self, response):
        print "Parse Product Called"
        product = ProductItem()
        # Parse name
        name = self._parse_name(response)
        product['name'] = name

        # Parse brand
        brand = self._parse_brand(response)
        product['brand'] = brand

        # Parse image
        image = self._parse_image(response)
        product['image'] = image
        product['link'] = response.url

        # Parse model
        model = self._parse_model(response)
        product['model'] = model

        # Parse categories
        categories = self._parse_categories(response)
        product['categories'] = categories

        # Parse unspec DOUBT DOUBT
        # unspec = self._parse_unspec(response)
        # product['unspec'] = unspec

        # Parse currencycode
        product['currencycode'] = 'GBP'

        # Set locale
        product['locale'] = 'en-UK'

        # Parse price
        price = self._parse_price(response)
        product['price'] = price

        # Parse price
        sku = self._parse_sku(response)
        product['sku'] = sku

        # Parse retailer_key
        retailer_key = self._parse_retailer_key(response)
        product['retailer_key'] = retailer_key

        # Parse stock status
        stock_status = self._parse_stock_status(response)
        product['productstockstatus'] = stock_status

        # Parse gallery
        gallery = self._parse_gallery(response)
        product['gallery'] = gallery

        # Parse features
        features = self._parse_features(response)
        product['features'] = features

        # Parse condition
        product['condition'] = 1

        return product

    @staticmethod
    def _parse_name(response):
        name = response.xpath("//h1[@class='page-title nosp']//text()").extract()
        if name:
            name = ''.join(name)
            name = ' '.join(name.split())
            return name

    @staticmethod
    def _parse_brand(response):
        brand = response.xpath("//script[@type='application/ld+json'][2]") \
            .xpath("text()").extract()[0].encode('utf-8').replace("\n", "").replace(" ", "").strip()
        json_data = json.loads(brand.replace("\"priceCurrency\":\"GBP\"}}", "}}"))
        brand = json_data['brand']['name']

        if brand:
            return brand

    @staticmethod
    def _parse_sku(response):
        sku = response.xpath("//script[@type='application/ld+json'][2]") \
            .xpath("text()").extract()[0].encode('utf-8').replace("\n", "").replace(" ", "").strip()
        json_data = json.loads(sku.replace("\"priceCurrency\":\"GBP\"}}", "}}"))
        sku = json_data['sku']

        if sku:
            return sku

    def _parse_stock_status(self, response):
        stock_status = response.xpath("//script[@type='application/ld+json'][2]") \
            .xpath("text()").extract()[0].encode('utf-8').replace("\n", "").replace(" ", "").strip()
        json_data = json.loads(stock_status.replace("\"priceCurrency\":\"GBP\"}}", "}}"))
        stock_status = json_data['offers']['availability']
        if stock_status:
            stock_status = stock_status.replace("http://schema.org/", "").strip()
            if stock_status == 'InStock':
                return self.STOCK_STATUS['IN_STOCK']
            elif stock_status == 'InStoreOnly':
                return self.STOCK_STATUS['CALL_FOR_AVAILABILITY']
            elif stock_status == 'OutOfStock':
                return self.STOCK_STATUS['OUT_OF_STOCK']
            else:
                return self.STOCK_STATUS['CALL_FOR_AVAILABILITY']

    @staticmethod
    def _parse_retailer_key(response):
        retailer_key = response.xpath("//p[@class='prd-code']/text()").extract()[0] \
            .replace("Product code: ", "").encode('utf-8')
        if retailer_key:
            return retailer_key

    @staticmethod
    def _parse_image(response):
        image = response.xpath("//a[@class='to-print MagicZoomPlus']//img[@class='product-image']/@src").extract()
        if image:
            return image[0]

    @staticmethod
    def _parse_model(response):
        model = response.xpath("//div[@class='section space-b']").xpath("ul//li[contains(.,'MPN')]/text()").extract()
        if model:
            return model[0]

    @staticmethod
    def _parse_categories(response):
        categories = response.xpath("//div[@class='breadcrumb']/a/span/text()").extract()
        if categories:
            categories.remove(u'Home')
            # model = '|'.join(model)
            return categories

    @staticmethod
    def _parse_price(response):
        price = response.xpath("//strong[@data-key='current-price']/text()").extract()
        if price:
            x = price[0].encode('utf8')
            x = x[2:]
            return x

    @staticmethod
    def _parse_gallery(response):
        gallery = response.xpath("//div[@id='carousel']//li/a/@href").extract()
        return gallery

    @staticmethod
    def _parse_features(response):
        features = []
        features_name = response.xpath("//table[@class='simpleTable']/tbody/tr/th/text()").extract()
        features_value = response.xpath("//table[@class='simpleTable']/tbody/tr/td")

        for f_name in features_name:
            index = features_name.index(f_name)
            features_value_content = features_value[index].xpath('text()').extract()[0]
            if features_value_content:
                features_value_content = features_value_content
            feature = {f_name: features_value_content} if features_value_content else {f_name: ""}
            features.append(feature)

        return features

    def _scrape_total_matches(self, response):
        # print "Scrape Total Matches Called"
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        totals = response.xpath("//section[@class='col9']/div/div/strong/text()").extract()
        totals = ''.join(totals).strip()
        if totals:
            totals = re.search("(\d+) results", str(totals))
            if totals:
                totals = totals.group(1).replace(',', '').replace('.', '').strip()
                if totals.isdigit():
                    if not self.TOTAL_MATCHES:
                        self.TOTAL_MATCHES = int(totals)
                    return int(totals)

    def _scrape_product_links(self, response):
        # print "Scrape Product Links Called"
        link_list = []
        if self.retailer_id:
            data = requests.get(self.API_URL.format(retailer_id=self.retailer_id)).json()
            for link in data:
                link = link['product_link']
                link_list.append(link)
            for link in link_list:
                url = link
                yield (url, ProductItem())
        else:
            links = response.xpath("//header[@class='productTitle']/a/@href").extract()
            for link in links:
                yield link, ProductItem()

    def _scrape_next_results_page_link(self, response):
        # print "Scrape Next Results Page Called"
        if self.retailer_id:
            return None
        search_term = response.meta['search_term']
        self.current_page += 1
        if self.current_page < math.ceil(self.TOTAL_MATCHES / 50.0):
            next_page = self.SEARCH_URL.format(search_term=search_term, page_num=self.current_page)
            return next_page
