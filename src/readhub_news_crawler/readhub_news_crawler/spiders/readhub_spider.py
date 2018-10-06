import scrapy
import time

class newsItem(scrapy.Item):
    id = scrapy.Field()
    date = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    source = scrapy.Field()
    
class readhubSpider(scrapy.Spider):
    name = "readhub"
    start_urls = ['https://readhub.me']

    def parse(self, response):
        item = newsItem()
        all_news = response.xpath('//*[@id="itemList"]/div')
        for news in all_news:
            date = time.strftime("%d-%m-%Y")
            title = news.css('div.topicItem___3YVLI h2.topicTitle___1M353 span.content___2vSS6::text').extract()
            links = news.css('div.articleItem___2P-7U a.articleTitle___3zy5I::attr(href)').extract()
            
            item['id'] = date + "-" + str(hash(title[0]))
            item['date'] = date
            item['title'] = title
            item['content'] = news.css('div.summary___1i4y3 div.bp-pure___3xB_W::text').extract()
            item['source'] = ";".join(links)
            yield item
            
        