
# Daily Digest in Chinese

![](/logo/skill_page.png)

This Alexa skill broadcasts the latest Chinese news from [ReadHub](https://readhub.me/). Enable this skill on your [Echo](https://www.amazon.com/all-new-amazon-echo-speaker-with-wifi-alexa-dark-charcoal/dp/B06XCM9LJ4) device to help you stay tuned with the latest technology news.

Please be aware that the news is broadcast in Chinese.


If you have an echo product, you can [enable this skill](https://www.bioconductor.org/packages/cytofkit/) to try and test, or play with it [here](https://echosim.io/) if you don't! 

Welcome feedback and suggestions!


# How is This Made

## Create a Spider to crawl the news from readhub.com

### Creating a scrapy project

```
scrapy startproject readhub_news_crawler
```

### Create our spider class

> Spiders are classes that you define and that Scrapy uses to scrape information from a website (or a group of websites). They must subclass scrapy.Spider and define the initial requests to make

create a file named `readhub_spider.py` under `readhub_news_crawler/spiders/` with following codes:


```
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
            
```

### Put our spider to work

Go to the project’s top level directory and run:

```
scrapy crawl readhub -t csv -o "readhub.csv" --loglevel=INFO
```

## install keda xunfei

Download `xunfei_tts` from 

```
bash 64bit_make.sh
```

## install lame

download from [lame v3.100](https://sourceforge.net/projects/lame/files/lame/3.100/)

```
make -f Makefile.unix
```