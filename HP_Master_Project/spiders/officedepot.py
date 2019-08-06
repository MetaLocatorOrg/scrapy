from __future__ import division, absolute_import, unicode_literals

import json
import re
import urlparse
import string

from HP_Master_Project.utils import clean_list
from scrapy import Request
from scrapy.log import WARNING

from HP_Master_Project.items import ProductItem
from HP_Master_Project.spiders import BaseProductsSpider, cond_set, \
    cond_set_value
from HP_Master_Project.utils import is_empty
from HP_Master_Project.extract_brand import extract_brand_from_first_words


class OfficedepotProductsSpider(BaseProductsSpider):
    name = 'officedepot_products'
    allowed_domains = ["officedepot.com", "www.officedepot.com", 'bazaarvoice.com', "store.hp.com"]
    start_urls = []

    SEARCH_URL = "http://www.officedepot.com/catalog/search.do?Ntt={search_term}&searchSuggestion=true&akamai-feo=off"

    API_URL = 'https://admin.metalocator.com/webapi/api/matchedretailerproducturls?Itemid=8343' \
              '&apikey=f5e4337a05acceae50dc116d719a2875&username=fatica%2Bscrapingapi@gmail.com' \
              '&password=8y3$u2ehu2e..!!$$&retailer_id={retailer_id}'

    PAGINATE_URL = 'http://www.officedepot.com/catalog/search.do?Ntx=mode+matchpartialmax&Nty=1&Ntk=all' \
                   '&Ntt={search_term}&N=5&recordsPerPageNumber=24&No={nao}'

    CURRENT_NAO = 0
    PAGINATE_BY = 24  # 24 products
    TOTAL_MATCHES = None  # for pagination

    def __init__(self, *args, **kwargs):
        self.user_agent = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36'
                           ' (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36')
        super(OfficedepotProductsSpider, self).__init__(
            site_name=self.allowed_domains[0], *args, **kwargs)

    def _parse_single_product(self, response):
        return self.parse_product(response)

    @staticmethod
    def _get_product_id(url):
        match = re.search(r'/products/(\d{2,20})/', url)
        if match:
            return match.group(1)

    def parse_product(self, response):
        meta = response.meta
        product = meta.get('product', ProductItem())

        # Parse locate
        locale = 'en_US'
        cond_set_value(product, 'locale', locale)

        # Parse name
        name = self.parse_name(response)
        cond_set(product, 'name', name, conv=string.strip)

        # Parse image
        image = self.parse_image(response)
        cond_set(product, 'image', image)

        # Parse brand
        brand = self.parse_brand(response)
        cond_set_value(product, 'brand', brand)

        # Parse sku
        sku = self.parse_sku(response)
        cond_set_value(product, 'sku', sku)

        # Parse price
        price = self.parse_price(response)
        cond_set_value(product, 'price', price)

        # Parse sale price
        product['saleprice'] = price

        # Parse model
        model = self._parse_model(response)
        cond_set_value(product, 'model', model)

        # Parse gallery
        gallery = self._parse_gallery(response)
        product['gallery'] = gallery

        # Parse stock status
        oos = self._parse_product_stock_status(response)
        cond_set_value(product, 'productstockstatus', oos)

        # Parse categories
        categories = self._parse_categories(response)
        cond_set_value(product, 'categories', categories)

        # Parse manufacturer
        manufacturer = self._parse_manufacturer(response)
        cond_set_value(product, 'manufacturer', manufacturer, conv=string.strip)

        # Parse shipping phrase
        shipping_phrase = self._parse_shippingphrase(response)
        product['shippingphrase'] = shipping_phrase

        # Parse ship to store
        ship_to_store = self._parse_shiptostore(response)
        product['shiptostore'] = ship_to_store

        # Parse retailer_key
        retailer_key = self._parse_retailer_key(response)
        product['retailer_key'] = retailer_key

        # Parse features
        features = self._parse_features(response)
        product['features'] = features

        return product

    def clear_text(self, str_result):
        return str_result.replace("\t", "").replace("\n", "").replace("\r", "").replace(u'\xa0', ' ').strip()

    def _parse_product_stock_status(self, response):
        product = response.meta['product']
        stock_value = self.STOCK_STATUS['CALL_FOR_AVAILABILITY']

        try:
            
            stock_message = response.xpath('//div[contains(@class,"discontinued")]//div[contains(@class,"no_longer_avail")]/text()').extract()
            if stock_message:
                stock_message = stock_message[0]
                if 'no longer available' in stock_message.lower():
                    stock_value = self.STOCK_STATUS['OUT_OF_STOCK']
                    
                product['productstockstatus'] = stock_value
                return product                
                
            stock_message = response.xpath('//meta[@itemprop="availability"]/@content').extract()
            if stock_message:
                stock_message = stock_message[0]
                if 'instock' in stock_message.lower():
                    stock_value = self.STOCK_STATUS['IN_STOCK']
                elif 'outofstock' in stock_message.lower():
                    stock_value = self.STOCK_STATUS['OUT_OF_STOCK']

                product['productstockstatus'] = stock_value
                return product

        except BaseException as e:
            self.log("Error parsing stock status data: {}".format(e), WARNING)
            product['productstockstatus'] = stock_value
            return product

    @staticmethod
    def _parse_model(response):
        model = response.xpath(
            '//*[@id="attributemodel_namekey"]/text()').extract()
        if model:
            return model[0].strip()

    @staticmethod
    def _parse_gallery(response):
        image_list = []
        if response.xpath('//script[@id="skuImageData"]/text()'):
            image_data = response.xpath('//script[@id="skuImageData"]/text()')[0].extract()
            image_data = json.loads(image_data)
            image_len = len(image_data)
            for i in range(image_len):
                image_url = 'http://s7d1.scene7.com/is/image/officedepot/' + image_data['image_' + str(i)]
                image_list.append(image_url)
        if image_list:
            return image_list
        return None

    @staticmethod
    def _parse_categories(response):
        categories = response.xpath(
            '//*[@id="siteBreadcrumb"]//'
            'span[@itemprop="name"]/text()').extract()
        return categories

    @staticmethod
    def parse_brand(response):
        brand = is_empty(response.xpath(
            '//td[@itemprop="brand"]/@content').extract())
        if not brand:
            brand = is_empty(response.xpath(
                '//td[@itemprop="brand"]/text()').extract())
        if brand:
            brand = brand.strip()
        return brand

    @staticmethod
    def parse_name(response):
        title = response.xpath('normalize-space(//div[@itemtype="http://schema.org/Product"]//h1[contains(@itemprop, "name")]//text())').extract()
        
        #out of stock products have a different selector
        if isinstance(title, list):
            title = response.xpath('normalize-space(//div[@id="skuTop"]//h1[contains(@class, "fn")]//text())').extract()
            
        #out of stock products have a different selector
        if not title:
            title = response.xpath('normalize-space(//div[@id="skuTop"]//h1[contains(@class, "fn")]//text())').extract()
  
        if title:
            return title

    def parse_data(self, response):
        data = re.findall(r'var MasterTmsUdo \'(.+)\'; ', response.body_as_unicode())
        if data:
            data = re.sub(r'\\(.)', r'\g<1>', data[0])
            try:
                js_data = json.loads(data)
            except:
                return
            return js_data

    @staticmethod
    def parse_image(response):
        img = response.xpath('//img[contains(@id, "mainSkuProductImage")]/@src').extract()
        return img

    def parse_sku(self, response):
        sku = response.xpath('//td[contains(@id, "basicInfoManufacturerSku")]/text()').extract()
        if sku:
            return self.clear_text(sku[0])

    @staticmethod
    def _parse_manufacturer(response):
        manufacture = response.xpath('//*[@itemprop="manufacturer"]/text()').extract()
        if manufacture:
            return manufacture[0]

    @staticmethod
    def parse_price(response):
        price = response.xpath('//meta[@itemprop="price"]/@content').extract()
        if price:
            return float(price[0].replace(",", "").replace("$", ""))

    def _parse_retailer_key(self, response):
        retailer_key = response.xpath('//td[contains(@id, "basicInfoCustomerSku")]/text()').extract()
        if retailer_key:
            return self.clear_text(retailer_key[0])

    @staticmethod
    def _parse_shippingphrase(response):
        shipping_phrase = response.xpath('//div[@class="deliveryMessage"]/text()').extract()
        if shipping_phrase:
            return shipping_phrase[0]

    def _parse_shiptostore(self, response):
        if self._parse_shippingphrase(response):
            return 1

        return 0

    def _parse_features(self, response):
        features = []
        features_name = response.xpath('//div[contains(@data-ccs-cc-inline-acc-idm, "specification")]'
                                       '//td[contains(@class, "specification-attribute")]/text()').extract()
        features_value = response.xpath('//div[contains(@data-ccs-cc-inline-acc-idm, "specification")]'
                                        '//td[not(contains(@class, "specification-attribute"))]/text()').extract()
        features_value = clean_list(self, features_value)

        for f_name in features_name:
            index = features_name.index(f_name)
            feature = {f_name: features_value[index]}
            features.append(feature)

        return features

    def parse_paginate_link(self, response, nao):
        check_page = '&No=%s' % nao
        for link in response.xpath(
                '//a[contains(@class, "paging")]/@href'
        ).extract():
            if check_page in link:
                u = urlparse.urlparse(link)
                return urlparse.urljoin('http://www.officedepot.com', u.path)

    def parse_category_link(self, response):
        categories_links = []
        for link in response.xpath(
                '//div[contains(@class, "category_wrapper")]/a[contains(@class, "link")]/@href'
        ).extract():
            categories_links.append(link)

    def _scrape_total_matches(self, response):
        if self.retailer_id:
            data = json.loads(response.body)
            return len(data)

        totals = response.xpath('//div[contains(@id, "resultCnt")]/text()').extract()
        if totals:
            totals = totals[0].replace(',', '').replace('.', '').strip()
            if totals.isdigit():
                if not self.TOTAL_MATCHES:
                    self.TOTAL_MATCHES = int(totals)
                return int(totals)

    def _get_products(self, response):
        if "officedepot.com/a/products" in response.url:
            response.meta['product'] = {}
            prod = self.parse_product(response)
            yield prod
        else:
            for req_or_prod in super(OfficedepotProductsSpider, self)._get_products(response):
                yield req_or_prod

    def _scrape_product_links(self, response):
        link_list = []
        if self.retailer_id:
            data = json.loads(response.body)
            for link in data:
                link = link['product_link']
                if 'officedepot' in link:
                    link_list.append(link)
            for link in link_list:
                yield link, ProductItem()
        else:
            links = response.xpath(
                '//div[contains(@class, "descriptionFull")]//a[contains(@class, "med_txt")]/@href'
            ).extract() or response.css('.desc_text a::attr("href")').extract()

            for link in links:
                yield link, ProductItem()

    def _get_nao(self, url):
        nao = re.search(r'nao=(\d+)', url)
        if not nao:
            return
        return int(nao.group(1))

    def _replace_nao(self, url, new_nao):
        current_nao = self._get_nao(url)
        if current_nao:
            return re.sub(r'nao=\d+', 'nao=' + str(new_nao), url)
        else:
            return url + '&nao=' + str(new_nao)

    def _scrape_next_results_page_link(self, response):
        if self.retailer_id:
            return
        if self.TOTAL_MATCHES is None:
            self.log('No "next result page" link!')
            return

        if self.CURRENT_NAO > self.quantity + self.PAGINATE_BY:
            return
        self.CURRENT_NAO += self.PAGINATE_BY
        if '/a/browse/' in response.url:  # paginate in category or subcategory
            new_paginate_url = self.parse_paginate_link(response, self.CURRENT_NAO)
            if new_paginate_url:
                return Request(new_paginate_url, callback=self.parse, meta=response.meta, dont_filter=True)
        return Request(
            self.PAGINATE_URL.format(
                search_term=response.meta['search_term'],
                nao=str(self.CURRENT_NAO)),
            callback=self.parse, meta=response.meta,
            dont_filter=True
        )
