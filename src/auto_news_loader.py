# -*- coding: utf-8 -*-
import re
import os
import csv
import uuid
import time
import boto3
import shutil
import argparse
import subprocess

s3 = boto3.client('s3')



def generate_working_dir(working_dir_base):
    """
    Creates a unique working directory to combat job multitenancy
    :param working_dir_base: base working directory
    :return: a unique subfolder in working_dir_base with a uuid
    """

    working_dir = os.path.join(working_dir_base, str(uuid.uuid4()))
    try:
        os.makedirs(working_dir)
    except Exception as e:
        print ('Can\'t creat folder %s' % working_dir)
        return working_dir_base
    return working_dir



def delete_working_dir(working_dir):
    """
    Deletes working directory
    :param working_dir:  working directory
    """

    try:
        shutil.rmtree(working_dir)
    except Exception as e:
        print ('Can\'t delete %s' % working_dir)



def news_loader(bucket_key, bucket_path, working_dir):

    date = time.strftime("%d-%m-%Y")
    print("Start news scrawling at: " + date)
    working_dir = generate_working_dir(working_dir)

    ## crawl data
    scrapy_output_file = os.path.join(working_dir, date + ".csv")
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
        out_txt_file = os.path.join(working_dir, "fresh_news_" + str(news_id) + ".txt")
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
        out_wav_file = os.path.join(working_dir, "fresh_news_" + str(news_id) + ".wav")
        try:
            subprocess.call(["mytts", in_txt.encode("gb2312"), out_wav_file, "xiaoyan"])
        except Exception:
            print("Message translate to audio failed!")
            continue

        ## trancode wav to mp3 and compress
        out_mp3_file = os.path.join(working_dir, "fresh_news_" + str(news_id) + ".mp3")
        subprocess.call(["lame", out_wav_file, out_mp3_file])

        ## uploaded to AWS S3 (bucket: fresh-news)
        print("Upload news audio to S3")
        mp3_s3_key = bucket_path + "/" + out_mp3_file
        s3.upload_file(out_mp3_file, bucket_key, mp3_s3_key)
        s3.put_object_acl(ACL='public-read', Bucket=bucket_key, Key= mp3_s3_key)
        
        news_id += 1

    f.close()
    print('Cleaning up working dir')
    delete_working_dir(working_dir)
                   

def main():
    parser = argparse.ArgumentParser('Daily Digest - Alexa Skill')
    parser.add_argument('--bucket_key', default = 'haoeric-daily-digest-news-audio', type=str, help='Bucket name where audio file will be saved', required=True)
    parser.add_argument('--bucket_path', default = 'fresh-news', type=str, help='file path above bucket', required=True)
    parser.add_argument('--working_dir', type=str, help='code working directory', default='/scratch')
    args = parser.parse_args()

    news_loader(args.bucket_key, args.bucket_path, args.working_dir)
    

if __name__ == '__main__':
    main()