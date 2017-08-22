# -*- coding: utf-8 -*-
import scrapy
import base64

from scrapy_splash import SplashRequest
from mlocator.items import MlocatorItem


class UscostcoSpider(scrapy.Spider):
	name = "uscostco"
	allowed_domains = ["costco.com"]
	#start_urls = ['https://www.costco.com/CatalogSearch?brand=hp&refine=750431&keyword=HP']
	#allowed_domains = ["lumtest.com"]
	#start_urls = ['https://lumtest.com/myip.json']
	#crawlera_enabled = True
	#crawlera_apikey = 'bdea5cf50015480185ab6844bc31c8e7'
	#export http_proxy="http://5RX8Pt:uvgCAE@196.19.159.99:8000"
	custom_settings = {
        'DOWNLOAD_DELAY' : 1.5
	}
	SEARCH_URL = 'https://www.costco.com/CatalogSearch?brand=hp&refine=750431&keyword=HP' 
	#HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "	"Chrome/60.0.3112.90 Safari/537.36"}
	HEADERS = {"User-Agent": 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0'}
	
	def start_requests(self):
		yield scrapy.Request(
			url=self.SEARCH_URL, callback=self.parse, dont_filter=True, headers=self.HEADERS
		)

	def parse(self, response):
		#print response.text
		NEXTPG_XP	= ".//li[@class='forward']/a/@href"
		PRD_XP		= ''
		PRDLNK_XP	= ".//a[@class='thumbnail']/@href"

		nextpg_lnk	= response.xpath(NEXTPG_XP).extract_first()
		prdct_lnks	= response.xpath(PRDLNK_XP).extract()
		for p_lnk in prdct_lnks: #remove bracketes on golive
			#print p_lnk
			#yield scrapy.Request(url=p_lnk, callback=self.parse_prod_page, headers=self.HEADERS)
			yield SplashRequest(url=p_lnk, callback=self.parse_prod_page, endpoint='render.html', 
				args={'wait': 0.5,
					"proxy":"http://5RX8Pt:uvgCAE@196.19.159.99:8000"})
		#print len(prdct_lnks)
		if nextpg_lnk:
			#print "8"*80, "\n", "Moving to next page", "\n", "8"*80
			yield scrapy.Request(url=nextpg_lnk, callback=self.parse, headers=self.HEADERS)

	def parse_prod_page(self, response):
		#PRD_TITLE_XP	= './/div[@id="product-details"]//h1/text()'
		PRD_TITLE_XP	= './/h1/text()'
		PRD_IMGS_XP		= './/img[@id="initialProductImage"]/@src'
		PRD_GLRY_XP		= './/*[@class="RICHFXColorChangeViewName"]/../img/@src'
		PRD_GLRY_XP		= './/img[@class[contains(.,"RICHFXColorChangeView")]]/@src'
		PRD_PRICE_XP	= './/div[@id="product-details"]//span[@class="op-value"]/text()'
		PRD_RTKEY_XP	= './/div[@class="scProdId"]/@sc.prodid'
		PRD_RTSKU_XP	= './/*[@class="item-number"]/span/@data-sku'
		PRD_MODEL_XP	= './/div[@id="product-details"]//span/@data-model-number'
		PRD_FEATRS_XP	= './/div[@class="product-info-specs"]/ul/li'
		#PRD_FEATRS_XP	= './/div[@class="product-info-specs"]/ul/li'
		PRD_STCK_XP		= './/div[@id="breakdown"]/div/@data-inv'
		#PRD_CATS_XP		= './/ul[@itemprop="breadcrumb"]/li[last()]/a/text()'
		PRD_CATS_XP		= './/ul[@class="crumbs"]/li/a/text()'
		PRD_SHPHRSE_XP	= './/*[@id="shipping-statement"]//text()'
		PRD_BRAND_XP	= './/*[@class="product-info-specs"]/ul/li[span="Brand:"]/text()'
		PRD_MMBRSHP_XP	= './/*[@id="product-details"]/p[@class="member-only"]'

		item = MlocatorItem()
		item["name"]				= response.xpath(PRD_TITLE_XP).extract_first()#.strip()
		item["link"]				= response.url
		item["image"]				= response.xpath(PRD_IMGS_XP).extract_first()
		item["price"]				= base64.b64decode(response.xpath(PRD_PRICE_XP).extract_first()) #use this price with Splash addon
		#item["price"]				= response.xpath(PRD_PRICE_XP).extract_first() # use this price without Splash addon
		#item["onlineonly"]			= ""
		item["model"]				= response.xpath(PRD_MODEL_XP).extract_first()
		item["brand"]				= "".join(response.xpath(PRD_BRAND_XP).extract()).strip()
		#item["instore"]				= ""
		#item["shiptostore"]			= ""
		item["currency"]			= "USD"
		item["retailer_sku"]		= response.xpath(PRD_RTSKU_XP).extract_first()
		item["retailer_key"]		= response.xpath(PRD_RTKEY_XP).extract_first()
		item["locale"]				= "en-US" #response.headers['Content-Language']
		gallery						= response.xpath(PRD_GLRY_XP).extract()
		item["gallery"]				= []
		for img in gallery: item["gallery"].append(img.replace("=735","=729"))
		item["shippingphrase"]		= response.xpath(PRD_SHPHRSE_XP).extract_first()
		features					= response.xpath(PRD_FEATRS_XP)
		item["features"] 			= {}
		for feature in features:
			#item["features"].append({feature.xpath("./td[1]":feature.xpath("./td[2]"))})
			index = feature.xpath("./span/text()").extract_first()
			value = ''.join(feature.xpath("./text()").extract()).strip()
			item["features"].update({index:value})
		item["categories"]			= "|".join(response.xpath(PRD_CATS_XP).extract()[1:])
		if response.xpath(PRD_MMBRSHP_XP): 	item["membershiprequired"]	= 1 
		else: item["membershiprequired"] = 0
		if "".join(response.xpath(PRD_STCK_XP).extract()) == 'IN_STOCK':
			item["productstockstatus"]	= 1
		#elif "".join(response.xpath(PRD_STCK_XP).extract()) == 'prod_stock_number isOutOfStock':
		#	item["productstockstatus"]	= 0
		else:
			item["productstockstatus"]	= "".join(response.xpath(PRD_STCK_XP).extract())

		yield item
