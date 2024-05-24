import pytest
import json
import boto3
import os

from deepdiff import DeepDiff


dirname = os.path.dirname(__file__)


UTILITIES_QUEUE_NAME = os.environ.get("UTILITIES_QUEUE_NAME")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
DYNAMO_TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME")

AWS_CONFIG = {
    "aws_access_key_id": "YOUR_AWS_ACCESS_KEY",
    "aws_secret_access_key": "YOUR_AWS_SECRET_KEY",
    "region_name": "eu-west-1",
}


@pytest.fixture
def get_state_machine():
    sfn_client = boto3.client(
        "stepfunctions",
        endpoint_url="http://step-functions:8083",
        **AWS_CONFIG,
    )

    response = sfn_client.list_state_machines(
        maxResults=123,
    )

    state_machine = [sm for sm in response["stateMachines"] if sm["name"] == "HelloWorld"].pop()

    yield {
        "state_machine": state_machine,
        "client": sfn_client
    }


@pytest.fixture
def get_queue_url_and_client():
    sqs_client = boto3.client(
        "sqs",
        endpoint_url="http://localstack:4566",
        **AWS_CONFIG,
    )

    queue = sqs_client.get_queue_url(
        QueueName=UTILITIES_QUEUE_NAME
    )

    yield {
        "queue_url": queue["QueueUrl"],
        "client": sqs_client,
    }


@pytest.fixture
def mock_s3():
    s3_client = boto3.client(
        "s3",
        endpoint_url="http://localstack:4566",
        **AWS_CONFIG
    )

    yield {"client": s3_client}


@pytest.fixture
def get_dynamo_client():
    dynamo_client = boto3.client(
        "dynamodb",
        endpoint_url="http://localstack:4566",
        **AWS_CONFIG
    )

    return {
        "client": dynamo_client
    }


class TestAWSIntegration:
    def test_adds_triage_successfully(
        self,
        mock_s3,
        get_dynamo_client
    ):
        bucket_contents = mock_s3["client"].get_object(
            Bucket=BUCKET_NAME, Key="execution_name_test/debug/data.json"
        )

        assert bucket_contents["Body"]
        assert json.loads(bucket_contents["Body"].read()) == {
            "message_payload": "Hello, World!"
        }

        dynamo_item = get_dynamo_client["client"].query(
            TableName=DYNAMO_TABLE_NAME,
            KeyConditions={
                "ExecutionName": {
                    "AttributeValueList": [{"S": "execution_name_test"}],
                    "ComparisonOperator": "EQ",
                }
            },
        )

        assert len(dynamo_item["Items"]) == 1
        assert dynamo_item["Items"][0]["Payload"] == {"S": "Hello, World!"}

        object_key = "execution_name_test/sec-response-schedule-d-7-b-1.json"
        sec_s3_content = mock_s3["client"].get_object(
            Bucket=BUCKET_NAME, Key=object_key
        )
        assert sec_s3_content["Body"]

        expected_result_file_path = os.path.join(dirname, './responses/schedule_d_7_b_1.json')
        with open(expected_result_file_path) as f:
            fetched_sec_content = json.loads(sec_s3_content["Body"].read())
            fetched_sec_fund_names = sorted([fund["1a-nameOfFund"] for fund in fetched_sec_content])

            expected_sec_content = json.load(f)
            expected_sec_fund_names = sorted([fund["1a-nameOfFund"] for fund in expected_sec_content])

            diff = DeepDiff(fetched_sec_fund_names, expected_sec_fund_names)
            assert not diff, f"Differences found: {diff}"
            f.close()
