# aws-apigateway-proxy-app

## Use Case
AWS customer applications with complex technology dependencies may operate in hybrid and multi-cloud environments that require application network connectivity between AWS resources and non-AWS domains.  For security conscious organizations that have a DENY-by-default mindset, this has traditionally meant firewall rules whitelisting application traffic to various AWS services as well as other software hosted in AWS.  This can increase the operational security overhead for the rules over time as new application services are added, existing services are changed, and old services are removed.  This can also result in application friction and lack of agility because application changes require network security changes to be implemented.  Furthermore, consider a SaaS context where these on-premise resources are communicating back to SaaS software hosted in AWS; hence, there is serious  operational complexity of making network security changes across the SaaS customer set when there are major application updates.

## Architecture
![AWS API Gateway Proxy Architecture](./img/aws-apigateway-proxy-customdomain.png)

This AWS API Gateway Proxy solution architecture solves this application network surface area problem by simplifying application traffic dependencies from external environments to AWS by using a single custom domain that the organization manages for network security, performance, and corporate brand requirements.  This solution is composed of Amazon Route53, Amazon Certificate Manager, Amazon Simple Storage Service (S3), Amazon CloudFront, and AWS API Gateway.  First and foremost, the solution minimzes the number of distinct AWS services that must be whitelisted for on-premise firewall rules.  The solution also centralizes DNS traffic scoped through a domain controlled by the organization using Route53, scales for large file uploads and downloads using CloudFront and S3, and finally enables application agility because API Gateway delivers convenient, low-code-no-code integration with native AWS services.

## Setup

### 00

### 01. Amazon Route53 DNS
* Create public hosted zone for your domain (e.g. `xyzware.io`)

### 02. Amazon Certificate Manager
* Create public Certificate scoped for resource (e.g. `proxy.xyzware.io`) or wild-card (e.g. `*.xyzware.io`) if the certificate will cover the CDN proxy, API, UI, as well as other public resources.  Use DNS validation.

### 03. Amazon Simple Storage Service (S3)
* Create S3 bucket for your application (e.g. `objectstorage-xyzware-io.xyzware.io`)
* Block public access to bucket (e.g. this is the best practice and most secure)
* Set empty IAM bucket policy (e.g. default is `DENY`)

### 04. API Gateway
* Create API Gateway instance
    ** API Type = `REST`
    ** API Name = `Xyzware API`
    ** Endpoint Type = `Regional`
* Create API Gateway Resource for mocks
    ** Name = `Mock`
    ** Path = `/mock`
    ** Method = `GET`
    ** Type = `Mock`
* Create API Gateway Resource for SQS
* Create API Gateway Resource for DynamoDB
* Create API Gateway Resource for Kinesis
* Deploy REST API Gateway Instance
* Test REST API Resources and Methods

[TODO] Custom Authorizer for API Gateway ... see References section
[TODO] AWS resources and methods for AWS services

### 05. Amazon CloudFront
* Create CloudFront distribution which will serve as the proxy entry point
* Add alternate domain name(s) corresponding to required resource name (e.g. `proxy.xyzware.io`)
* Add CNAME record to hosted zone for this public resource(s) (e.g. `proxy.xyzware.io`)
* Create distribution origin associated with the S3 bucket created earlier (e.g. `objectstorage-xyzware-io.xyzware.io`) using `Origin Access - Public`.
* Define default distribution behavior for the S3 origin with the following settings:
    ** Path pattern = `*`
    ** Compress objects = `no`
    ** Viewer protocol policy = `Redirect HTTP to HTTPS`
    ** Allowed HTTP methods = `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`
    ** Restrict viewer access = `no`
    ** Cache key and origin requests = Cache policy = `Caching Disabled`; Origin Request custom policy = `Headers=None, Cookies=None, QueryStrings=All`
* Create distribution origin associated with the API Gateway created earlier.
* Define distribution behavior for API Gateway origin
    ** Path pattern = `api`
    ** Compress objects = `no`
    ** Viewer protocol policy = `Redirect HTTP to HTTPS`
    ** Allowed HTTP methods = `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`
    ** Restrict viewer access = `no`
    ** Cache key and origin requests = Cache policy = `Caching Disabled`; Origin Request custom policy = `Headers=None, Cookies=None, QueryStrings=All`

### 06. S3 Presigned URL Generator

You must create an API wrapper that will generate S3 presigned URLs for a specific S3 Bucket and Key within a region.  The request should contain the bucket and object key; the response should contain the corresponding S3 presigned URL.  These URLs are scoped to a specific action (e.g. GET, PUT, POST, DELETE) on the object.

In the Test section below, there are illustrative CLI examples for using the AWS CLI to generate URLs and then downloading files via the CloudFront distribution associated with S3.

## Build 

## Deploy 

## Test

### Test File Download and Upload

#### Download

$ cd src/demo
$ aws s3 presign s3://objectstorage-xyzware-io/helloworld.txt
https://objectstorage-xyzware-io.s3.us-east-2.amazonaws.com/helloworld.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAZMRMMBEC4QLMHJ66%2F20230110%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20230110T133408Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a45d8c650540942894ffb8c0bdf8b8c62c7f7de13ab0a60b2ffe46b0606fc8a9
$ curl -X GET "https://proxy.xyzware.io/helloworld.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAZMRMMBEC4QLMHJ66%2F20230110%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20230110T133408Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a45d8c650540942894ffb8c0bdf8b8c62c7f7de13ab0a60b2ffe46b0606fc8a9"

#### Upload

### Test Custom APIs

### Test AWS APIs

## References

* https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-integration-types.html
* https://docs.aws.amazon.com/general/latest/gr/s3.html
* https://docs.aws.amazon.com/general/latest/gr/apigateway.html
* https://aws.amazon.com/blogs/storage/using-presigned-urls-to-identify-per-requester-usage-of-amazon-s3/
* https://aws.amazon.com/blogs/compute/introducing-custom-authorizers-in-amazon-api-gateway/
* https://aws.amazon.com/blogs/compute/introducing-iam-and-lambda-authorizers-for-amazon-api-gateway-http-apis/
* https://aws.amazon.com/blogs/compute/managing-multi-tenant-apis-using-amazon-api-gateway/
* https://github.com/monken/aws-ecr-public
* https://github.com/jamesb3ll/s3-presigned-url-lambda
* https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-rest-api-sqs-errors/
* https://github.com/boto/boto3/issues/2477
* https://github.com/aws/aws-sdk-js/issues/669

## FAQ

