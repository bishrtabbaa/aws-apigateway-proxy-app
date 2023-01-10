# aws-apigateway-proxy-app

## Use Case
AWS customers with complex technology environments may operate hybrid and multi-cloud workloads that require application network connectivity between on-premise and AWS resources.  For security conscious organizations that have a DENY-by-default mindset, this has traditionally meant firewall rules whitelisting various AWS services as well as other software hosted in AWS.  This can increase the operational security overhead for the rules over time as new application services are added, existing services are changed, and old services are removed.  This can also result in application friction and lack of agility because application changes require network security changes to be implemented.  Furthermore, consider a SaaS context where these on-premise resources are communicating back to SaaS software hosted in AWS; there is serious  operational complexity of making network security changes across the SaaS customer set when there are major application updates.

## Architecture
![AWS API Gateway Proxy Architecture](./img/aws-apigateway-proxy-customdomain.png)

This AWS API Gateway Proxy reference architecture solves this network surface area problem by simplifying application traffic dependencies from external environments to AWS by using a custom domain that the organization controls for network security, performance, and corporate brand purposes.  This solution architecture is composed of Amazon Route53, Amazon Certificate Manager, Amazon Simple Storage Service (S3), and Amazon CloudFront, and AWS API Gateway.  The solution minimzes the number of distinct AWS services that must be whitelisted for on-premise firewall rules, centralizes DNS traffic scoped through a domain controlled by the organization using Route53, scales for large file uploads and downloads using CloudFront and S3, and finally enables technology agility because it uses API Gateway to deliver convenient, low-code-no-code integration with native AWS services.

## Setup

### Amazon Route53 DNS
* Create public hosted zone for your domain (e.g. `xyzware.io`)
* Add CNAME record to hosted zone for your expected resource(s) (e.g. `api.xyzware.io`)

### Amazon Certificate Manager
* Create public Certificate scoped for resource (e.g. `api.xyzware.io`) or wild-card (e.g. `*.xyzware.io`)

### Amazon Simple Storage Service (S3)
* Create S3 bucket for your application (e.g. `objectstorage-xyzware-io.xyzware.io`)
* Block public access to bucket
* Set empty IAM bucket policy (e.g. default is `DENY`)

### Amazon CloudFront
* Create CloudFront distribution.
* 

### API Gateway

## Build 

zip ../../package/mathly-lambda-package.zip *.py
zip ../../package/helloworld-lambda-package.zip *.py

## Deploy 

### Lambda Components

#### Create Function
aws lambda create-function --function XyzwareApiGatewayProxyMathlyFunction --zip-file fileb://mathly-lambda-package.zip --role arn:aws:iam::645411899653:role/service-role/MyLambdaExecutionRole --runtime python3.9 --package-type Zip --handler mathlyfunction.lambda_handler

aws lambda create-function --function XyzwareApiGatewayProxyHelloWorldFunction --zip-file fileb://helloworld-lambda-package.zip --role arn:aws:iam::645411899653:role/service-role/MyLambdaExecutionRole --runtime python3.9 --package-type Zip --handler helloworldfunction.lambda_handler

Lambda Edge must be in us-east-1 and IAM role must be assumable by both lambda.amazonaws.com and edgelambda.amazonaws.com

aws lambda create-function --function XyzwareApiGatewayProxyS3CloudfrontLambdaEdgeFunction --zip-file fileb://s3cfledge-lambda-package.zip --role arn:aws:iam::645411899653:role/service-role/MyLambdaExecutionRole --runtime python3.9 --package-type Zip --handler s3cfledgefunction.lambda_handler --region us-east-1


#### Update Function
aws lambda update-function-code --function XyzwareApiGatewayProxyMathlyFunction --zip-file fileb://mathly-lambda-package.zip
aws lambda update-function-code --function XyzwareApiGatewayProxyS3CloudfrontLambdaEdgeFunction --zip-file fileb://s3cfledge-lambda-package.zip