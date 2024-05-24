import pytest
import boto3
import os
import json


RUN_TESTS_QUEUE_NAME = os.environ.get("RUN_TESTS_QUEUE_NAME")


def run_tests(sfn_client, task_token):
    # The argument to pytest.main is a list of command line arguments.
    # This can include the path to the test files, and any pytest flags you need, e.g., -v for verbose.
    result = pytest.main(['-v', '.'])

    if result == 0:
        print("All tests passed!")
        sfn_client.send_task_success(
            taskToken=task_token,
            output=json.dumps({"success": True})
        )
    else:
        print("Some tests failed.")
        sfn_client.send_task_failure(
            taskToken=task_token,
            error=json.dumps({"success": False})
        )


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
        QueueName=RUN_TESTS_QUEUE_NAME,
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
        run_tests(sfn_client, json.loads(message["Body"])["task_token"])


start()
