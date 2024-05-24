import json
import boto3
# import time
import os


LOCAL_APP_QUEUE_NAME = os.environ.get("LOCAL_APP_QUEUE_NAME")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
DYNAMO_TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME")


def get_dynamodb_items(
    key: str, value: str, dynamo_client
) -> dict:
    try:
        response = dynamo_client.scan(
            TableName=DYNAMO_TABLE_NAME,
            ExpressionAttributeValues={
                ':a': {
                    'S': value,
                },
            },
            FilterExpression=f"{key} = :a"
        )
        items = response["Items"]
        return items[0]
    except Exception as exc:
        print(
            f"Failed to get items from DynamoDB table: {exc}"
        )
        raise exc


def write_to_dynamo(message):
    dynamo_client = boto3.client(
        "dynamodb",
        aws_access_key_id="YOUR_AWS_ACCESS_KEY",
        aws_secret_access_key="YOUR_AWS_SECRET_KEY",
        region_name="eu-west-1",
        endpoint_url="http://localstack:4566"
    )

    dynamo_record = get_dynamodb_items(
        key="ExecutionName",
        value="execution_name_test",
        dynamo_client=dynamo_client,
    )

    dynamo_record.update({
        "Payload": {"S": message.get("payload")}
    })

    dynamo_client.put_item(
        TableName=DYNAMO_TABLE_NAME,
        Item=dynamo_record,
    )


def write_to_s3(message):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id="YOUR_AWS_ACCESS_KEY",
        aws_secret_access_key="YOUR_AWS_SECRET_KEY",
        region_name="eu-west-1",
        endpoint_url="http://localstack:4566"
    )

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="execution_name_test/debug/data.json",
        Body=json.dumps({
            "message_payload": message["payload"]
        }).encode("utf-8"),
    )


def process_message(message):
    write_to_s3(message)
    write_to_dynamo(message)


def poll_queue(sqs_client, queue):
    messages = sqs_client.receive_message(
        QueueUrl=queue.get("QueueUrl"),
        WaitTimeSeconds=1,
    )

    if messages.get("Messages", None):
        return messages
    else:
        return poll_queue(sqs_client, queue)


def start() -> None:
    sqs_client = boto3.client(
        "sqs",
        aws_access_key_id="id",
        aws_secret_access_key="secret",
        region_name="eu-west-1",
        endpoint_url="http://localstack:4566"
    )

    queue = sqs_client.get_queue_url(
        QueueName=LOCAL_APP_QUEUE_NAME,
    )

    sfn_client = boto3.client(
        "stepfunctions",
        aws_access_key_id="id",
        aws_secret_access_key="secret",
        region_name="eu-west-1",
        endpoint_url="http://step-functions:8083"
    )

    messages = poll_queue(sqs_client, queue)

    for message in messages['Messages']:
        process_message(json.loads(message["Body"]))

        # # Let the queue know that the message is processed
        sqs_client.delete_message(
            QueueUrl=queue.get("QueueUrl"),
            ReceiptHandle=message.get("ReceiptHandle")
        )

        sfn_client.send_task_success(
            taskToken=json.loads(message["Body"])["task_token"],
            output=json.dumps({"success": True})
        )

start()
