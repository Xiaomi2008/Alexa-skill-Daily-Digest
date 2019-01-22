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
    start_urls = ['https://readhub.cn']

    def parse(self, response):
        item = newsItem()
        all_news = response.xpath('//*[@id="itemList"]/div')
        print("Total News crawlered: " + str(len(all_news)))
        for news in all_news:
            date = time.strftime("%d-%m-%Y")
            title = news.css('div.topicItem___1B0j1 h2.topicTitle___1HWIA a.content___3EhkM::text').extract()
            print(title)
            if len(title) > 0:
                links = news.css('div.articleItem___2P-7U a.articleTitle___3zy5I::attr(href)').extract()
                item['id'] = date + "-" + str(hash(title[0]))
                item['date'] = date
                item['title'] = title
                item['content'] = news.css('div.summary___3jny8 div.bp-pure___3xB_W::text').extract()
                item['source'] = ";".join(links)
                yield item
            
        