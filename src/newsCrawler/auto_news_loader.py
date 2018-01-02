import re
import os
import csv
import uuid
import time
import boto3
import schedule
import subprocess
from boto3.dynamodb.conditions import Key, Attr

DB_TABLE_NAME = 'news_snippet'
BUCKET_NAME = 'haoeric-pollyaudiofiles'
AUDIO_FOLDER = 'fresh-news'
s3 = boto3.client('s3')

def job():
    date = time.strftime("%d-%m-%Y")
    print("Start news scrawling at: " + date)
    scrapy_output_file = date + "-" + str(uuid.uuid4()) + ".csv"

    ## crawl data
    subprocess.call('scrapy crawl readhub -t csv -o ' + scrapy_output_file + ' --loglevel=INFO', shell = True)
    
    ## parse results
    f = open(scrapy_output_file, encoding='utf-8', newline='')
    reader = csv.DictReader(f)
    news_id = 1
    for row in reader:
        # id      = row['id']
        # date    = row['date']
        # source  = row['source']
        title   = row['title']
        content = row['content']
        
        in_txt = title + "。" + content
        out_wav_file = "fresh_news_" + str(news_id) + ".wav"
        out_mp3_file = "fresh_news_" + str(news_id) + ".mp3"

        ## tidy Chinese text
        r1 = u'[()（）【】「」《》“”‘’\[\]{}&\'*/<=>@★、^_{|} \s]+'
        in_txt= re.sub(r1, '', in_txt)

        r2 = u'[.]{3}'   
        in_txt= re.sub(r2, '。', in_txt)

        ## convert text to audio, gb2312 is the default incoding for xunfei tts SDK
        try:
            subprocess.call(["mytts", in_txt.encode("gb2312"), out_wav_file, "xiaoyan"])
        except Exception:
            print("Message translate to audio failed!")
            continue

        ## trancode wav to mp3 and compress
        subprocess.call(["lame", out_wav_file, out_mp3_file])

        ## uploaded to AWS S3
        print("Upload news audio to S3")
        s3_key = AUDIO_FOLDER + "/" + out_mp3_file
        s3.upload_file(out_mp3_file, BUCKET_NAME, s3_key)
        s3.put_object_acl(ACL='public-read', Bucket=BUCKET_NAME, Key= s3_key)

        ## remove audio file
        os.remove(out_wav_file)
        os.remove(out_mp3_file)

        ## update file id
        news_id += 1
    # f.close()
    os.remove(scrapy_output_file)
                   

def main():
    schedule.every(1).hours.do(job)
    #schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()


