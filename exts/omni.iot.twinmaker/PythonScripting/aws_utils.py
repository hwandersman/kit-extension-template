import boto3
import uuid
from .constants import DEFAULT_ASSUME_ROLE_ARN

def get_aws_client(service_name, region, assume_role_arn):
    if assume_role_arn == DEFAULT_ASSUME_ROLE_ARN:
        return boto3.client(service_name, region)

    sts_client = boto3.client('sts')
    response = sts_client.assume_role(
        RoleArn=assume_role_arn,
        RoleSessionName=f'nvidia-ov-session{uuid.uuid1()}',
        DurationSeconds=1800
    )
    new_session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken']
    )
    return new_session.client(service_name, region)