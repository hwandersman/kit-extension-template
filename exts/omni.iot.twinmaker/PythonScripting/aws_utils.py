import boto3
import uuid
from .constants import DEFAULT_ASSUME_ROLE_ARN

def getAWSClient(serviceName, region, assumeRoleARN):
    if assumeRoleARN == DEFAULT_ASSUME_ROLE_ARN:
        return boto3.client(serviceName, region)

    stsClient = boto3.client('sts')
    response = stsClient.assume_role(
        RoleArn=assumeRoleARN,
        RoleSessionName=f'nvidia-ov-session{uuid.uuid1()}',
        DurationSeconds=1800
    )
    newSession = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken']
    )
    return newSession.client(serviceName, region)