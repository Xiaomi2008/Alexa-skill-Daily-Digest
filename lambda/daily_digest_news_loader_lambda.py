from __future__ import print_function

import boto3
import json
import os
import re
import botocore

s3 = boto3.resource('s3')
batch_client = boto3.client('batch')


def check_file(s3_path):
    """
    Check if a S3 file exists
    :param s3_path: s3 object path
    :return: boolean
    """
    bucket = s3_path.split('/')[2]
    key = '/'.join(s3_path.split('/')[3:])
    try:
        s3.Object(bucket, key).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            exists = False
        else:
            raise
    else:
        exists = True
    return exists

def copy_manifest_file(s3_origin_path, s3_output_path):
    copy_source = {
      'Bucket': s3_origin_path.split('/')[2],
      'Key': '/'.join(s3_origin_path.split('/')[3:])
    }
    
    out_key = '/'.join(s3_output_path.split('/')[3:]) + "manifest_files/" + s3_origin_path.split('/')[-1]
    bucket = s3.Bucket(s3_output_path.split('/')[2])
    bucket.copy(copy_source, out_key)

    

    
def lambda_handler(event, context):
    # Log the received event
    print("Received event: " + json.dumps(event, indent=2))
    # Get parameters for the SubmitJob call
    # http://docs.aws.amazon.com/batch/latest/APIReference/API_SubmitJob.html

    ## check if resutls already existed, skip the job if T (True)
    if (event['overwrite_all'] == 'F' and event['Hallmark_adapterTrimmer']['overwrite_results'] == 'F'):
        adapterTrimmedFastq1 = event['results_s3_folder_path'] + event['sample_ID'] + "_R1_001_upstream_adapterTrimmed.fastq"
        adapterTrimmedFastq2 = event['results_s3_folder_path'] + event['sample_ID'] + "_R2_001_upstream_adapterTrimmed.fastq"
        trimmedFastq1Check = check_file(adapterTrimmedFastq1)
        trimmedFastq2Check = check_file(adapterTrimmedFastq2)
        if(trimmedFastq1Check and trimmedFastq2Check):
            event['jobId'] = "PASS"
            return event
    
    ## copy manifest files to results folder
    ## file and path rules are hard coded here, need improvement in the future
    print("Upload bed file")
    bed_path = event['bed_path']
    copy_manifest_file(bed_path ,event['results_s3_folder_path'])
    print("Upload R1 adapter file")
    r1_upstreamAdapter_path = event['r1_upstreamAdapter_path']
    copy_manifest_file(r1_upstreamAdapter_path ,event['results_s3_folder_path'])
    print("Upload R2 adapter file")
    r2_upstreamAdapter_path = event['r2_upstreamAdapter_path']
    copy_manifest_file(r2_upstreamAdapter_path ,event['results_s3_folder_path'])
    print("Upload R1 primer file")
    r1_upstream_targetPrimers_path = event['r1_upstream_targetPrimers_path']
    copy_manifest_file(r1_upstream_targetPrimers_path ,event['results_s3_folder_path'])
    
    command = ["--sample_ID", event['sample_ID'],
               "--fastq1_gz_path", event['fastq1_gz_path'],
               "--fastq2_gz_path", event['fastq2_gz_path'],
               "--extra_filling_seq", event['extra_filling_seq'],
               "--r1_upstreamAdapter_path", event['r1_upstreamAdapter_path'],
               "--r2_upstreamAdapter_path", event['r2_upstreamAdapter_path'],
               "--read_minimum_length", event['Hallmark_adapterTrimmer']['read_minimum_length'],
               "--results_s3_folder_path", event['results_s3_folder_path'],
               "--working_dir", event['working_dir'],
               "--is_S3_data", event['is_S3_data']
               ]

    job_name = '-'.join(['Hallmark_adapterTrimmer', event['sample_ID']])
    job_definition = event['Hallmark_adapterTrimmer']['jobDefinition']
    job_queue = event['Hallmark_adapterTrimmer']['jobQueue']
    container_overrides = {'command': command,}
    depends_on = event['dependsOn'] if event.get('dependsOn') else []

    try:
        response = batch_client.submit_job(
            jobDefinition=job_definition,
            jobName=job_name,
            jobQueue=job_queue,
            dependsOn=depends_on,
            containerOverrides=container_overrides
        )
        
        # Log response from AWS Batch
        print("Response: " + json.dumps(response, indent=2))
        
        # Return the jobId
        event['jobId'] = response['jobId']
        return event
    
    except Exception as e:
        print(e)
        message = 'Error submitting job - Hallmark_adapterTrimmer'
        print(message)
        raise Exception(message)
