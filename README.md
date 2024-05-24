# Step Definitions: Local Testing

## Overview:

This repo is an MVP for an investigation into replicating StepFunctions and accompanying
AWS infrastructure locally with defined test cases.

### Table of Contents:

- [Description](#description)
- [Utilities Setup](#utilities_setup)
- [Running Tests](#running_tests)
- [Reference Documentation](#reference_documentation)

## Description:

This repo runs the following AWS services locally:

- StepFunctions
- SecretsManager
- SQS
- S3
- DynamoDB

It runs a StepFunction definition referenced here: [test-definition](./test-definition.json)

The StepFunction invokes three Apps:
- a local app which ingests from SQS then writes to
Dynamo and S3.
- an existing app `Utilities` (which requires a bit of preparation, see below)
- a test runner, which reads from SQS then runs `pytest` which triggers the 
test to run which validates the data from the two apps in S3 and SQS

NOTE: The `Utilities` app will make a valid HTTP request to the SEC api and 
requires a valid SEC auth token in the `.env` file. The result from this api 
call will be "persisted" in S3 (localstack), then retrieved and validated in the
test suite. 


## Utilities Setup:

This test requires a locally build "Utilities" image. Boto3 requires an extra
attribute (`endpoint_url`) to run in this test environment. As this flow uses
S3, SQS, DynamoDB, SecretsManager and StepFunctions this attribute needs to be
added to each client.

### Steps:

1. Clone or pull latest main branch locally

2. In the repo open the file `utilities/app/sqs.py` and update the SQS and Step
Function Clients like so:

#### SQS Client Update:

```
        get_sqs_client.client = boto3.client(  # type: ignore[attr-defined]
            "sqs",
            region_name=settings.region,
            endpoint_url=os.getenv("SQS_ENDPOINT")
        )
```

#### StepFunctions Client Update:

```
        get_sfn_client.client = boto3.client(  # type: ignore[attr-defined]
            "stepfunctions",
            region_name=settings.region,
            endpoint_url=os.getenv("STEPFUNCTIONS_ENDPOINT_URL")
        )
```

- In the repo open the file `utilities/app/api/common/aws_handler.py` and update the S3, DynamoDB and SecretsManager Clients like so:

#### S3 Client Update:

```
            self._clients["s3"] = boto3.client(
                "s3",
                region_name=settings.region,
                endpoint_url=os.getenv("S3_ENDPOINT_URL")
            )
```

#### DynamoDB Client Update:

```
            self._clients["dynamodb"] = boto3.resource(
                "dynamodb",
                region_name=settings.region,
                endpoint_url=os.getenv("DYNAMO_ENDPOINT_URL")
            )
```

#### SecretsManager Client Update:

```
        client = session.client(
            service_name="secretsmanager",
            region_name=settings.region,
            endpoint_url=os.getenv("SECRETSMANAGER_ENDPOINT_URL")
        )
```

3. Build the image locally with following command:

```
docker build . -t utilities:1.0
```

## Running Tests:

1. Create a `.env` file and copy the `.example.env` over (only the SEC_API_KEY needs updating from example)
2. Make sure you've updated the `docker-compose.yml` to reference the correct 
utilities image name and version (default is set to `image: utilities:1.0`)
3. Run `docker compose up`
4. Tests should run and you should see:

```
============================== 1 passed in 0.16s ===============================
```

5. Update the file `tests/test_aws_pipeline.py` to deliberately fail and rerun to see
failure outcome

## Reference Documentation:

### LocalStack General:

- https://docs.localstack.cloud/user-guide/aws/sqs/
- https://docs.localstack.cloud/user-guide/aws/s3/
- https://docs.localstack.cloud/user-guide/aws/dynamodb/
- https://docs.localstack.cloud/user-guide/aws/secretsmanager/

### LocalStack Network Troubleshooting:

- https://docs.localstack.cloud/references/network-troubleshooting/endpoint-url/

### AWS Managed Step Function Image:
- https://hub.docker.com/r/amazon/aws-stepfunctions-local

### Boto3 General:

- https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

