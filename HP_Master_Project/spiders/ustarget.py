# -*- coding: utf-8 -*-
import scrapy
import json

from mlocator.items import MlocatorItem


class UscostcoSpider(scrapy.Spider):
	name = "ustarget"
	allowed_domains = ["target.com"]
	BRAND = "hp"
	COUNT = "24"
	start_urls = ['https://intl.target.com/s?searchTerm=hp#Nao=0&facetedValue=5wmdh&sortBy=relevance&og=hp']
	start_urls = ["https://redsky.target.com/v1/plp/search?keyword=%s&count=%s&offset=0&sort_by=relevance&channel=web&pageId=/s/" %(BRAND,COUNT)]

	#allowed_domains = ["lumtest.com"]
	#start_urls = ['https://lumtest.com/myip.json']
	#crawlera_enabled = True
	#crawlera_apikey = 'bdea5cf50015480185ab6844bc31c8e7'
	custom_settings = {
        'DOWNLOAD_DELAY' : 1.5
    }

	def parse(self, response):
		#first_req = scrapy.Request("https://redsky.target.com/v1/plp/search?keyword=%s&count=%s&offset=0&sort_by=relevance&channel=web&pageId=/s/" %(self.BRAND,self.COUNT))
		js = json.loads(response.text)
		total_results = int(js["search_response"]["metaData"][1]["value"])
		for i in range(total_results/int(self.COUNT)+1): #REMOVE ON GOLIVE
			nextpg_lnk = "https://redsky.target.com/v1/plp/search?keyword=%s&count=%s&offset=%s&sort_by=relevance&channel=web&pageId=/s/" %(self.BRAND,self.COUNT,str(int(self.COUNT)*i))
			#print nextpg_lnk
			yield scrapy.Request(url=nextpg_lnk, callback=self.parse_prod)

	def parse_prod(self, response):
		js = json.loads(response.text)
		for i in range(int(self.COUNT)):
			
			item = MlocatorItem()
			try: item["name"]				= js["search_response"]["items"]["Item"][i]["title"]
			except KeyError: pass
			try: item["image"]				= js["search_response"]["items"]["Item"][i]["images"][0]["base_url"] + js["search_response"]["items"]["Item"][i]["images"][0]["primary"]
			except KeyError: pass
			try: item["link"]				= "www." + self.allowed_domains[0] + js["search_response"]["items"]["Item"][i]["url"]
			except KeyError: pass
			try: item["upc"]				= js["search_response"]["items"]["Item"][i]["upc"]
			except KeyError: pass
			try: item["price"]				= js["search_response"]["items"]["Item"][i]["list_price"]["price"]
			except KeyError: pass
			try: item["saleprice"]			= js["search_response"]["items"]["Item"][i]["offer_price"]["price"]
			except KeyError: pass
			try: item["retailer_key"]		= js["search_response"]["items"]["Item"][i]["dpci"]
			except KeyError: pass
			try: item["instore"]			= int(js["search_response"]["items"]["Item"][i]["pick_up_in_store"])
			except KeyError: pass
			try: item["shiptostore"]		= int(js["search_response"]["items"]["Item"][i]["ship_to_store"])
			except KeyError: pass
			try: item["brand"]				= js["search_response"]["items"]["Item"][i]["brand"]
			except KeyError: pass
			try: productstockstatus			= js["search_response"]["items"]["Item"][i]["availability_status"]
			except KeyError: pass
			if (productstockstatus == "IN_STOCK") or (productstockstatus == "LIMITED_STOCK"):
				item["productstockstatus"] = 1
			else:
				item["productstockstatus"] = 0
			item["locale"]		= "en-US" 
			item["currency"]	= "USD"

			
			#try: gallery					= js["search_response"]["items"]["Item"][i]["images"][0]["alternate_urls"]
			#except KeyError: pass
			#if gallery: 
			#		gallery_list = []
			#		for img in gallery:
			#			gallery_list.append(js["search_response"]["items"]["Item"][i]["images"][0]["base_url"] + img)#
			#item["gallery"]				= gallery_list
			

			try: featrs					= js["search_response"]["items"]["Item"][i]["bullet_description"]
			except KeyError: pass
			##print features
			if featrs:
				item["features"] 			= {}
				for feature in featrs:
					index = feature.split(u":")[0].replace("<B>","")
					value = feature.split(u":")[1].replace("</B>","")
					item["features"].update({index:value})

			if  item["brand"].lower() == self.BRAND: yield item
			