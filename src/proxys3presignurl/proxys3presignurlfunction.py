"""
You must have an AWS account to use this Python code.
© 2022, Amazon Web Services, Inc. or its affiliates. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# file: proxys3presignurlfunction.py
# author: bishrt@amazon.com
# date: 01-18-2022

# IMPORTS
import boto3
import json
import os
import logging
from botocore.config import Config
from botocore.exceptions import ClientError

# CONSTANTS
S3_PRESIGN_URL_EXPIRATION = 10000
FORMAT_S3_ENDPOINT_URL = "https://s3.{}.amazonaws.com"
FORMAT_S3_BUCKET_URL = "https://{}.s3.{}.amazonaws.com"

# LOGGER
logger = logging.getLogger()
# logger.handler == console
csh = logging.StreamHandler()
logger.addHandler(csh)
# logger.level
logger.setLevel(logging.INFO)

# ASSUME current runtime context has appropriate networking connectivity and IAM permissions in AWS account

def str2bool(s):
    if (s != None):
        return s.lower() in ("yes", "y", "true", "t", "1")
    else:
        return False

def generate_s3_presign_proxy_url(s3_client, method, parameters, expiration):
    return s3_client.generate_presigned_url(
        ClientMethod=method,
        Params=parameters,
        ExpiresIn=expiration
    )

def map_method_to_action(method):
    _method = method.lower()

    if("get" == _method):
        return "get_object"
    elif("put" == _method):
        return "put_object"
    elif("delete" == _method):
        return "delete_object"
    else:
        # raise EXCEPTION
        return None

# ENVIRONMENT VARIABLES 
# AWS_REGION : string, 
# PROXY_CLOUDFRONT_URL : string, https://proxy.xyzware.io
def lambda_handler(event, context):
    logger.info('Getting OS environment variables.')
    logger.info(os.environ)

    # response 
    responseStatusCode = 200
    responseMessage = None
    s3_presign_url = None
    proxy_presign_url = None
    bucket = None
    method = None
    key = None
    uploadId = None
    partNumber = None

    # environment variables
    region = None
    cloudfrontDistributionUrl = None
    
    try:
        region = os.environ['AWS_REGION']
    except KeyError:
        responseStatusCode = 500
        responseMessage = "You must set environment: AWS_REGION"

    try:
        cloudfrontDistributionUrl = os.environ['PROXY_CLOUDFRONT_URL']
    except KeyError:
        responseStatusCode = 500
        responseMessage = "You must set environment: PROXY_CLOUDFRONT_URL"    

    if (responseStatusCode == 200):
        # request parameters ... TODO VALIDATE ... handle errors
        if 'bucket' in event:
            bucket = event['bucket']
        if 'method' in event:
            method = event['method']
        if 'key' in event:
            key = event['key']
        if 'queryStringParameters' in event:
            if 'bucket' in event['queryStringParameters']:
                bucket = event['queryStringParameters']['bucket']
            if 'method' in event['queryStringParameters']:
                method = event['queryStringParameters']['method']
            if 'key' in event['queryStringParameters']:
                key = event['queryStringParameters']['key']

        # TODO ... MULTIPART

        # build urls
        s3_endpoint_url=FORMAT_S3_ENDPOINT_URL.format(region)
        s3_bucket_url = FORMAT_S3_BUCKET_URL.format(bucket,region)
        s3_client = boto3.client(service_name='s3', endpoint_url=s3_endpoint_url, config=Config(region_name=region,s3={'addressing_style':'virtual'}))
        client_method_action = map_method_to_action(method)
        s3_presign_url = s3_client.generate_presigned_url(
            ClientMethod=client_method_action,
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=S3_PRESIGN_URL_EXPIRATION
        )

        # log
        logger.info("S3 Presigned URL = " + s3_presign_url)
        proxy_presign_url = s3_presign_url.replace(s3_bucket_url,cloudfrontDistributionUrl)
        logger.info("Proxy Presigned URL = " + proxy_presign_url)

    # return response to APIGW
    return {
        "statusCode": responseStatusCode,
        "headers" : {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": responseMessage,
            "proxyPresignUrl" : proxy_presign_url,
            "s3PresignUrl" : s3_presign_url,
            "bucket" : bucket,
            "method" : method, 
            "key" : key
        })
    }