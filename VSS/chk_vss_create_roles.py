import boto3
import logging
import os
logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
This lambda function will be triggered on SQS queue event.
sqsqueue() will receive account id from SQS queue and role() will check
if cloudformation template 'vss_create_roles.yml' does exist in US-EAST-1 or not.
Environment variables:
CFRole -- This IAM role should be in remote accounts for remote account template creation
OrgCrossAcctAccessRole -- This role is from master account to STS Token generation.
queueurl -- URL of SQS Queue
'''

def sqsqueue(event):
    #Get account# and delete message from queue.
    sqs = boto3.client('sqs', region_name="us-east-1")
    for record in event['Records']:
        acct = record['body']
        msg_del = sqs.delete_message(QueueUrl=os.environ['queueurl'], ReceiptHandle = record['receiptHandle'])
    return acct

def role(event, context):

    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)

    account = sqsqueue(event)

    #Generate STS Token

    master_rolearn = "arn:aws:iam::"+ account +":role/" + str(os.environ['OrgCrossAcctAccessRole'])

    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
    RoleArn=master_rolearn,
    RoleSessionName="AssumeRoleSession1")

    credentials=assumed_role_object['Credentials']

    #Generate Secret Access Key

    client = boto3.client('cloudformation',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken'], region_name='us-east-1')

    #Generate RoleARN for remote account CFT.

    roleARN = 'arn:aws:iam::'+ account + ':role/' + str(os.environ['CFRole'])

    #Check CFT exists and if not create CFT in remote account.
    bucket_url = 'https://'+str(os.environ['S3Bucket'])+'.s3.amazonaws.com/vss_create_roles.yml'
    cf_list = client.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])

    if len(cf_list['StackSummaries']) == 0:
        print ("Creating stack.....")
        response = client.create_stack(StackName='vss_create_roles', Capabilities=['CAPABILITY_IAM'], RoleARN=roleARN, TemplateURL=bucket_url)
    else:
        for i in range(len(cf_list['StackSummaries'])):
            if cf_list['StackSummaries'][i]['StackName'] == 'vss_create_roles' and cf_list['StackSummaries'][i]['StackStatus'] == "CREATE_COMPLETE":
                print ("Template does exists in account #{}." .format(account))
                break
            else:
                print ("Creating stack in Account#{}." .format(account))
                response = client.create_stack(StackName='vss_create_roles', Capabilities=['CAPABILITY_IAM'], RoleARN=roleARN, TemplateURL=bucket_url)
