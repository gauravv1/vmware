import boto3
import logging
import os
logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
This lambda function will generate accounts id from CSO Default OU in AWS Organizations
and send those ids to SQS Queues.
Environment variable:
queueurl -- SQS Queue
'''

def lambda_handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)

    accounts = []
    sqs = boto3.client('sqs', region_name="us-east-1")
    orgclient = boto3.client('organizations')
    ou_r = orgclient.list_roots()['Roots'][0]
    parent = orgclient.list_organizational_units_for_parent(ParentId=ou_r['Id'])
    while True:
        for ou in parent['OrganizationalUnits']:
            if 'CSO Default' in ou['Name']:
                CSO_id=ou['Id']
        if 'NextToken' in parent:
            parent = orgclient.list_organizational_units_for_parent(ParentId=ou_r['Id'], MaxResults=2, NextToken=parent['NextToken'])
        else:
            break

    CSO_accts = orgclient.list_accounts_for_parent(ParentId=CSO_id)
    while True:
        for accts in CSO_accts['Accounts']:
           accounts.append(str(accts['Id']))
        if 'NextToken' in CSO_accts:
            CSO_accts = orgclient.list_accounts_for_parent(ParentId=CSO_id, MaxResults=100, NextToken=CSO_accts['NextToken'])
        else:
            break

    for account in range(len(accounts)):
        response = sqs.send_message(QueueUrl=os.environ['queueurl'], MessageBody=accounts[account])
    print("Accounts numbers generation completed.")
