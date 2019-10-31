import boto3
import json
import logging, os
'''
This lambda function will generate DynamoDB table which will be used by
AWS Accounts team.
Lambda will take JSON data from S3 and update records in DynamoDB Table.
Environment Variables:
file: JSON File Name
S3Bucket: S3 Bucket name
'''
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def record(event, context):

    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)

    s3 = boto3.resource('s3')

    content_object = s3.Object(os.environ['S3Bucket'], os.environ['file'])
    file_content = content_object.get()['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)

    dynamo = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamo.Table(os.environ['DynamoTableName'])

    print (len(json_content))
    for i in range(len(json_content)):
        rec = {}
        for j in range(len(json_content[i]["tags"])):
            rec[str(json_content[i]["tags"][j]['key'])] = str(json_content[i]["tags"][j]['value'])
        rec['id'] = str(json_content[i]['owner_id'])
        res = table.put_item(Item=rec)
        print(res['ResponseMetadata']['HTTPStatusCode'])
