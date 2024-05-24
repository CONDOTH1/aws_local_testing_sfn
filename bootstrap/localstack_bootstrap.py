import boto3
import os
import json


def create_queue(queue_name):
    # Configure boto3 to use LocalStack
    sqs = boto3.client(
        "sqs",
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        endpoint_url=os.getenv('SQS_ENDPOINT_URL')
    )

    # Create the SQS queue
    response = sqs.create_queue(
        QueueName=queue_name
    )
    print(f"Queue Created: {response['QueueUrl']}")


def create_secrets(secret_name, secrets):
    secrets_client = boto3.client(
        "secretsmanager",
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        endpoint_url=os.getenv('SECRETSMANAGER_ENDPOINT_URL')
    )

    secrets_client.create_secret(
        Name=secret_name,
        SecretString=json.dumps(secrets),
    )
    print("Secret for SEC saved")


def create_state_machine():
    # dirname = os.path.dirname(__file__)
    dirname = os.path.dirname(os.path.abspath("__file__"))

    filename = os.path.join(dirname, './test-definition.json')

    sfn_client = boto3.client(
        "stepfunctions",
        endpoint_url=os.getenv('STEPFUNCTIONS_ENDPOINT_URL')
    )

    with open(filename) as f:
        data = json.dumps(json.load(f))
        state_machine = sfn_client.create_state_machine(
            name="HelloWorld",
            definition=data,
            roleArn="arn:aws:iam::012345678901:role/DummyRole"
        )
        f.close()

    print(f"State Machine successfully created: {state_machine}")

    execution_result = sfn_client.start_execution(
        stateMachineArn=state_machine["stateMachineArn"],
        input=json.dumps({
            "run_tests_queue_url": os.getenv("RUN_TESTS_QUEUE_URL"),
            "local_app_queue_url": os.getenv("LOCAL_APP_QUEUE_URL"),
            "queue_url": os.getenv("SQS_QUEUE_URL"),
            "CRD": "361",
            "s3_bucket": os.environ.get("BUCKET_NAME")
        }),
        name="execution_name_test",
    )

    print(f"Started the execution {execution_result}")


def create_dynamo():
    DYNAMO_TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME")
    dynamo_client = boto3.client(
        "dynamodb",
        endpoint_url=os.getenv('DYNAMO_ENDPOINT_URL')
    )

    dynamo_client.create_table(
        AttributeDefinitions=[
            {"AttributeName": "ExecutionName", "AttributeType": "S"},
        ],
        TableName=DYNAMO_TABLE_NAME,
        KeySchema=[
            {"AttributeName": "ExecutionName", "KeyType": "HASH"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    result = dynamo_client.put_item(
        TableName=DYNAMO_TABLE_NAME,
        Item={
            "ExecutionName": {"S": "execution_name_test"},
        },
    )
    print(f"Dynamo table successfully created and item added: {result}")


def create_s3():
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.getenv('S3_ENDPOINT_URL')
    )
    result = s3_client.create_bucket(
        Bucket=os.environ.get("BUCKET_NAME"),
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )
    print(f"S3 bucket successfully created and item added: {result}")


create_dynamo()
create_queue(os.getenv('UTILITIES_QUEUE_NAME'))
create_queue(os.getenv('LOCAL_APP_QUEUE_NAME'))
create_queue(os.getenv('RUN_TESTS_QUEUE_NAME'))
create_secrets(
    secret_name="/local/withintelligence/sec",
    secrets={"SEC_API_KEY": os.getenv('SEC_API_KEY')},
)
create_s3()

# Needs To Happen After Queues Created
create_state_machine()
