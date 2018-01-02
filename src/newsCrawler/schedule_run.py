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

def job():
    print("I'm working...")
    date = time.strftime("%d-%m-%Y")
    scrapy_output_file = date + "-" + str(uuid.uuid4()) + ".csv"
    ## crawl data
    subprocess.call('scrapy crawl readhub -t csv -o ' + scrapy_output_file + ' --loglevel=INFO', shell = True)
    
    ## parse results
    f = open(scrapy_output_file, encoding='utf-8', newline='')
    reader = csv.DictReader(f)
    for row in reader:
        id      = row['id']
        date    = row['date']
        title   = row['title']
        content = row['content']
        source  = row['source']
        
        ## check if already recorded in DynomoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(DB_TABLE_NAME)
        s3 = boto3.client('s3')
        
        ## if item not in DynomoDB
        if table.query(KeyConditionExpression=Key('id').eq(id))['Count'] < 1:
            ## update to DynomoDB
            table.put_item(Item={
                'id' : id,
                'date': date,
                'title' : title,
                'content' : content,
                'source' : source,
                'status' : 'PROCESSING'})

            
            in_txt = title + ". " + content
            out_wav_file = id + ".wav"
            out_mp3_file = id + ".mp3"

            ## tidy chinese text
            ## remove non utf-8 encoding characters
            #f = re.compile(u'[^\u4E00-\u9FA5A-Za-z0-9_\uFF0C\u3002\uFF1F\uFF01]')
            #in_txt = f.sub(r' ', in_txt)
            ## remove unnecessary punctuation and symbols
            #r = u'[’!"#¥$%&\'()*,./\;<=>@★、…【】「」《》“”‘’[\\]^_`{|}~ \s]+'
            #r = u'[ \s]+'
            #in_txt= re.sub(r, '', in_txt)
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
            s3_key = date + "/" + out_mp3_file
            s3.upload_file(out_mp3_file, BUCKET_NAME, s3_key)
            s3.put_object_acl(ACL='public-read', Bucket=BUCKET_NAME, Key= s3_key)

            ## get S3 url
            location = s3.get_bucket_location(Bucket=BUCKET_NAME)
            region = location['LocationConstraint']
            if region is None:
                url_begining = "https://s3.amazonaws.com/"
            else:
                url_begining = "https://s3-" + str(region) + ".amazonaws.com/"
            url = url_begining + BUCKET_NAME + "/" + s3_key

            ## Updating audio url and status in DynamoDB
            table.update_item( Key={'id':id},
                  UpdateExpression="SET #statusAtt = :statusValue, #urlAtt = :urlValue",                   
                  ExpressionAttributeValues={':statusValue': 'UPDATED', ':urlValue': url},
                  ExpressionAttributeNames={'#statusAtt': 'status', '#urlAtt': 'url'},
                  )
            
            os.remove(out_wav_file)
            os.remove(out_mp3_file)
        else:
            print("This news has already been processed!")
    # f.close()
    os.remove(scrapy_output_file)
                   

def main():
    #schedule.every(1).minutes.do(job)
    schedule.every(4).hours.do(job)
    # schedule.every().day.at("10:30").do(job)
    # schedule.every(5).to(10).minutes.do(job)
    # schedule.every().monday.do(job)
    # schedule.every().wednesday.at("13:15").do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()

