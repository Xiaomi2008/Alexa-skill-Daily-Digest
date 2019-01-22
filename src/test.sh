## test scrapy crawler
scrapy crawl readhub -t csv -o /Users/chenhao/Downloads/readhub_news.csv --loglevel=INFO



## test docker, generate results locally
docker run -t -v /Users/chenhao/Downloads:/out_data -w=/ -t daily_digest_alexa --bucket_key haoeric-daily-digest-news-audio --bucket_path fresh-news --working_dir /out_data