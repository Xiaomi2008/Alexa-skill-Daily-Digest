# -*- coding: utf-8 -*-
import re
import os
import csv
import uuid
import time
import boto3
import argparse
import subprocess

s3 = boto3.client('s3')

def news_loader(bucket_key, bucket_path):

    date = time.strftime("%d-%m-%Y")
    print("Start news scrawling at: " + date)

    ## crawl data
    scrapy_output_file = date + "-" + str(uuid.uuid4()) + ".csv"
    subprocess.call('scrapy crawl readhub -t csv -o ' + scrapy_output_file + ' --loglevel=INFO', shell = True)
    
    ## parse results
    f = open(scrapy_output_file, encoding='utf-8', newline='')
    reader = csv.DictReader(f)
    news_id = 1
    for row in reader:
        id      = row['id']
        date    = row['date']
        title   = row['title']
        content = row['content']
        source  = row['source']
        
        ## tidy Chinese text
        in_txt = title + "。" + content
        r1 = u'[()（）【】「」《》“”‘’\[\]{}&\'*/<=>@★、^_{|} \s]+'
        in_txt = re.sub(r1, '', in_txt)
        r2 = u'[.]{3}'   
        in_txt = re.sub(r2, '。', in_txt)
        in_txt = " "*5 + in_txt

        ## save txt to file and upload to S3
        out_txt_file = "fresh_news_" + str(news_id) + ".txt"
        txt_file_handler = open(out_txt_file, 'w')
        txt_file_handler.write(id +'\n')
        txt_file_handler.write(in_txt +'\n')
        txt_file_handler.write(date +'\n')
        txt_file_handler.write(source +'\n')
        txt_file_handler.close()

        print("Upload news txt to S3")
        txt_s3_key = bucket_path + "/" + out_txt_file
        s3.upload_file(out_txt_file, bucket_key, txt_s3_key)
        s3.put_object_acl(ACL='public-read', Bucket=bucket_key, Key= txt_s3_key)

        ## convert text to audio, gb2312 is the default incoding for xunfei tts SDK
        out_wav_file = "fresh_news_" + str(news_id) + ".wav"
        try:
            subprocess.call(["mytts", in_txt.encode("gb2312"), out_wav_file, "xiaoyan"])
        except Exception:
            print("Message translate to audio failed!")
            continue

        ## trancode wav to mp3 and compress
        out_mp3_file = "fresh_news_" + str(news_id) + ".mp3"
        subprocess.call(["lame", out_wav_file, out_mp3_file])

        ## uploaded to AWS S3 (bucket: fresh-news)
        print("Upload news audio to S3")
        mp3_s3_key = bucket_path + "/" + out_mp3_file
        s3.upload_file(out_mp3_file, bucket_key, mp3_s3_key)
        s3.put_object_acl(ACL='public-read', Bucket=bucket_key, Key= mp3_s3_key)

        os.remove(out_wav_file)
        os.remove(out_mp3_file)
        news_id += 1

    f.close()
    os.remove(scrapy_output_file)
                   

def main():
    parser = argparse.ArgumentParser('Daily Digest - Alexa Skill')
    parser.add_argument('--bucket_key', default = 'haoeric-daily-digest-news-audio', type=str, help='Bucket name where audio file will be saved', required=True)
    parser.add_argument('--bucket_path', default = 'fresh-news', type=str, help='file path above bucket', required=True)
    args = parser.parse_args()

    news_loader(args.bucket_key, args.bucket_path)
    

if __name__ == '__main__':
    main()