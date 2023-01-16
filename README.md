# aws-apigateway-proxy-app

## Use Case
AWS customer applications with complex technology dependencies may operate in hybrid and multi-cloud environments that require application network connectivity between AWS resources and non-AWS domains.  For security conscious organizations that have a ___DENY-by-default___ mindset, this has traditionally meant firewall rules whitelisting application traffic to various AWS services as well as other software hosted in AWS.  This can increase the operational security overhead for the rules over time as new application services are added, existing services are changed, and old services are removed.  This can also result in application friction and lack of agility because application changes require network security changes to be implemented.  Furthermore, consider a SaaS context where these on-premise resources are communicating back to SaaS software hosted in AWS; hence, there is serious  operational complexity of making network security changes across the SaaS customer set when there are major application updates.

## Architecture
![AWS API Gateway Proxy Architecture](./img/aws-apigateway-proxy-customdomain.png)

This AWS API Gateway Proxy solution architecture solves this application cloud network surface area problem by simplifying application traffic dependencies from external environments to AWS by using a ___single custom domain___ that the organization manages for network security, performance, and corporate brand requirements.  This solution is composed of Amazon Route53, Amazon Certificate Manager, Amazon Simple Storage Service (S3), Amazon CloudFront, and AWS API Gateway.  

First and foremost, the solution ___minimzes___ the number of distinct AWS services that must be whitelisted for on-premise firewall rules.  The solution also ___centralizes___ DNS traffic scoped through a domain controlled by the organization using Route53, ___scales___ for large file uploads and downloads using CloudFront and S3, and finally ___enables___ application agility because API Gateway delivers convenient, low-code-no-code integration with native AWS services.

## Setup

### 00 [TODO]

### 01. Amazon Route53 DNS
* Create public hosted zone for your domain (e.g. `xyzware.io`)

### 02. Amazon Certificate Manager
* Create public Certificate scoped for resource (e.g. `proxy.xyzware.io`) or wild-card (e.g. `*.xyzware.io`) if the certificate will cover the CDN proxy, API, UI, as well as other public resources.  Use DNS validation.

### 03. Amazon Simple Storage Service (S3)
* Create S3 bucket for your application (e.g. `objectstorage-xyzware-io.xyzware.io`)
* Block public access to bucket (e.g. this is the best practice and most secure)
* Set empty IAM bucket policy (e.g. default is implicit `DENY`)

### 04. API Gateway
* Create API Gateway (APIGW) instance
    * API Type = `REST`
    * API Name = `Xyzware API`
    * Endpoint Type = `Regional`
* Create APIGW Resource api 
    * Name = `/api`
* Create API Gateway Resource for mocks
    * Resource Name = `Mock`
    * Path = `/api/mock`
    * Method = `GET`
    * Type = `Mock`
* Create API Gateway Resource for DynamoDB
    * Resource Name = `/api/ddb/tenants`
    * Method = `GET`
        * Integration Type = `AWS`
        * Region = (e.g. `us-east-2`)
        * Service = `DynamoDB`
        * Method = `POST` (this may be counter-intuitive however it accords with the DDB API)
        * Action = `Scan`
        * Mapping Template = Content-Type = `application/json`; Passthrough = `when there are no templates defined (recommended)`; 
        Template = `{"TableName":"Tenants"}` (note this is template case-sensitive)
    * Method = `PUT`
        * Integration Type = `AWS`
        * Region = (e.g. `us-east-2`)
        * Service = `DynamoDB`
        * Method = `POST` (this may be counter-intuitive however it accords with the DDB API)
        * Action = `PutItem`
        * Mapping Template = Content-Type = `application/json`; this is case-sensitive and specific to your DynamoDB table. Template = ```{ 
        "TableName": "Tenants",
        "Item": 
        { 
        "TenantId": {"S": "$context.requestId" },
        "IsActive": {"BOOL": "$input.path('$.IsActive')"},
        "Name": {"S": "$input.path('$.Name')" },
        "Tier": {"S": "$input.path('$.Tier')"}
        }
        }```
    * Reference = https://aws.amazon.com/blogs/compute/using-amazon-api-gateway-as-a-proxy-for-dynamodb/
* Create API Gateway Resource for SQS
* Create API Gateway Resource for Kinesis
* Deploy REST API Gateway Instance to a specific stage (e.g. `dev`, `prod`, etc.)
* Create custom domain name for APIGW and map to specific APIGW instance stage
    * Domain Name = `api.xyzware.io`
    * Instance Mapping = `XYZWare API` (e.g. refers to instance created earlier `https://ou734xvpw2.execute-api.us-east-2.amazonaws.com/`)
    * Instance Stage = (e.g. `dev`, `prod`, etc.)
* Create Route53 CNAME entry that points from the custom domain name (e.g. `api.xyzware.io`) to the newly created custom domain endpoint `d-y2x5azvr8e.execute-api.us-east-2.amazonaws.com`)
* Test REST API Resources and Methods
    * `curl -X GET https://api.xyzware.io/api/mock`

[TODO] Custom Authorizer and Security for API Gateway ... see References section
[TODO] other AWS resources and methods for AWS services

### 05. Amazon CloudFront
* Create CloudFront distribution which will serve as the ___proxy entry point___ to the solution.
* Add alternate domain name(s) corresponding to required resource name (e.g. `proxy.xyzware.io`)
* Add CNAME record to R53 hosted zone for this public resource(s) (e.g. from `proxy.xyzware.io` to `d1jpuj2baecazo.cloudfront.net`)
* Create distribution origin associated with the S3 bucket created earlier (e.g. `objectstorage-xyzware-io.xyzware.io`) using `Origin Access - Public`.
* Define default distribution behavior for the S3 origin with the following settings:
    * Path pattern = `*`
    * Compress objects = `no`
    * Viewer protocol policy = `Redirect HTTP to HTTPS`
    * Allowed HTTP methods = `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`
    * Restrict viewer access = `no`
    * Cache key and origin requests = Cache policy = `Caching Disabled`; then define Origin Request custom policy = `Headers=None, Cookies=None, QueryStrings=All`
* Create distribution origin associated with the API Gateway created earlier.
    * Domain = DNS name of API Gateway (e.g. `api.xyzware.io`
    * Protocol = `HTTPS Only`
    * Port = `443`
    * Origin path = stage of API Gateway (e.g. `dev` or `prod`)
* Define distribution behavior for API Gateway origin
    * Path pattern = `/api/*`
    * Compress objects = `no`
    * Viewer protocol policy = `HTTPS only`
    * Allowed HTTP methods = `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`
    * Restrict viewer access = `no`
    * Cache key and origin requests = `Legacy Settings`; Headers = `None`; Query Strings = `None`; Cookies = `None`; Object caching = `Use origin cache headers`

### 06. S3 Presigned URL Generator

You must create an API wrapper that will generate S3 presigned URLs for a specific S3 Bucket and Key within a region.  The request should contain the bucket and object key; the response should contain the corresponding S3 presigned URL.  These URLs are scoped to a specific action (e.g. GET, PUT, POST, DELETE) on the object.

In the Test section below, there are illustrative CLI examples for using the AWS CLI to generate URLs and then downloading files via the CloudFront distribution associated with S3.

## Build 

## Deploy 

## Test

### Test File Download and Upload

#### Download

```
$ cd src/demo
$ aws s3 presign s3://objectstorage-xyzware-io/helloworld.txt
https://objectstorage-xyzware-io.s3.us-east-2.amazonaws.com/helloworld.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAZMRMMBEC4QLMHJ66%2F20230110%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20230110T133408Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a45d8c650540942894ffb8c0bdf8b8c62c7f7de13ab0a60b2ffe46b0606fc8a9
$ curl -X GET "https://proxy.xyzware.io/helloworld.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAZMRMMBEC4QLMHJ66%2F20230110%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20230110T133408Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a45d8c650540942894ffb8c0bdf8b8c62c7f7de13ab0a60b2ffe46b0606fc8a9"
```

#### Upload

### Test Custom APIs

* Test REST API Resources and Methods
    * `curl -X GET "https://proxy.xyzware.io/api/mock"`
    * `curl -X GET "https://proxy.xyzware.io/api/ddb/tenants/"`

### Test AWS APIs

## References

* https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-integration-types.html
* https://docs.aws.amazon.com/general/latest/gr/s3.html
* https://docs.aws.amazon.com/general/latest/gr/apigateway.html
* https://aws.amazon.com/blogs/storage/using-presigned-urls-to-identify-per-requester-usage-of-amazon-s3/
* https://aws.amazon.com/blogs/compute/introducing-custom-authorizers-in-amazon-api-gateway/
* https://aws.amazon.com/blogs/compute/introducing-iam-and-lambda-authorizers-for-amazon-api-gateway-http-apis/
* https://aws.amazon.com/blogs/compute/managing-multi-tenant-apis-using-amazon-api-gateway/
* https://aws.amazon.com/blogs/compute/using-amazon-api-gateway-as-a-proxy-for-dynamodb/
* https://github.com/monken/aws-ecr-public
* https://github.com/jamesb3ll/s3-presigned-url-lambda
* https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-cloudfront-distribution/
* https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-domain-cloudfront/
* https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-rest-api-sqs-errors/
* https://github.com/boto/boto3/issues/2477
* https://github.com/aws/aws-sdk-js/issues/669

## FAQ

