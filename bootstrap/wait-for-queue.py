import boto3
import os
import time


def wait_for_queue(queue_name, endpoint_url):
    sqs = boto3.client('sqs', endpoint_url=endpoint_url)
    while True:
        try:
            sqs.get_queue_url(QueueName=queue_name)
            print(f"SQS queue '{queue_name}' is now available.")
            break
        except sqs.exceptions.QueueDoesNotExist:
            print(f"Waiting for SQS queue '{queue_name}' to be available...")
            time.sleep(1)


if __name__ == "__main__":
    utilities_queue_name = os.getenv('UTILITIES_QUEUE_NAME')
    local_app_queue_name = os.getenv('LOCAL_APP_QUEUE_NAME')
    local_app_queue_name = os.getenv('RUN_TESTS_QUEUE_NAME')
    endpoint_url = os.getenv('AWS_ENDPOINT')
    wait_for_queue(utilities_queue_name, endpoint_url)
    wait_for_queue(local_app_queue_name, endpoint_url)
