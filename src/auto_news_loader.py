# -*- coding: utf-8 -*-
import re
import os
import csv
import uuid
import time
import boto3
import shlex
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


def upload_folder(s3_path, local_folder_path, sse=True):
    """
    Uploads a local folder to S3
    :param s3_path: s3 path to upload folder to
    :param local_folder_path: local folder path
    :param sse: boolean whether to enable server-side encryption
    """
    cmd = 'aws s3 cp --recursive %s %s --acl public-read' % (local_folder_path, s3_path)

    if sse:
        cmd += ' --sse'

    subprocess.check_call(shlex.split(cmd))


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
    
    upload_to_s3 = False
    if working_dir == "/scratch":
        upload_to_s3 = True

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
        
        ## tidy up Chinese text
        in_txt = title + '。' + content
        ## remove unicode, not supported by xunfei tts
        r1 = u'[【】「」《》“”‘’\[\]{}&\'*/<=>@★^_{|} \s]+'
        in_txt = re.sub(r1, '', in_txt)
        ## remove ... at the end of the news
        r2 = u'[.]{3}'   
        in_txt = re.sub(r2, '。', in_txt)
        ## add pause between news
        if news_id > 1:
            in_txt = ':'*5 + in_txt
        else:
            in_txt = '今日新闻:' + in_txt
            
        ## save txt to file
        out_txt_file = os.path.join(working_dir, "fresh_news_" + str(news_id) + ".txt")
        txt_file_handler = open(out_txt_file, 'w')
        txt_file_handler.write(id +'\n')
        txt_file_handler.write(in_txt +'\n')
        txt_file_handler.write(date +'\n')
        txt_file_handler.write(source +'\n')
        txt_file_handler.close()
    
        ## convert text to audio, gb2312 is the default incoding for xunfei tts SDK
        out_wav_file = os.path.join(working_dir, "fresh_news_" + str(news_id) + ".wav")
        try:
            subprocess.call(["mytts", in_txt.encode("gb2312"), out_wav_file, "xiaoyan",
            "text_encoding = utf8, sample_rate = 16000, speed = 50, volume = 60, pitch = 50, rdn = 2"])
        except Exception:
            print("Message translate to audio failed!")
            continue

        ## trancode wav to mp3 and compress
        out_mp3_file = os.path.join(working_dir, "fresh_news_" + str(news_id) + ".mp3")
        subprocess.call(["lame", out_wav_file, out_mp3_file])

        news_id += 1

    f.close()

    if upload_to_s3:
        print("Upload news to S3")
        upload_folder("s3://" + bucket_key + "/" + bucket_path + "/", working_dir)
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