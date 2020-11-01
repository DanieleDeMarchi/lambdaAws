import json
import boto3
from boto3.dynamodb.conditions import Key
import os
from botocore.vendored import requests

#
# Lambda function che viene triggerata al momento della connessione e disconnessione di un dispositivo
# Salva lo stato del dispositivo in una tabella DynamoDB
#

def insertToDB(device_id, timestamp, evento, errorCode="", dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name="us-west-2")
    
    table = dynamodb.Table('Devices')
    response = table.update_item(
        Key={
            'device_id': device_id
        },
        UpdateExpression="set connection_status=:c, con_status_timestamp=:t, errorCode=:e",
        ExpressionAttributeValues={
            ':c': evento,
            ':t': timestamp,
            ':e': errorCode
        },
        ReturnValues="UPDATED_NEW"
    )
    return response
    

def lambda_handler(event, context):
    
    device_id = event["clientId"]
    timestamp = event["timestamp"]
    eventType = event["eventType"]
    if(eventType == "disconnected"):
        if(event["clientInitiatedDisconnect"] == False):
            insertToDB(device_id, timestamp, "disconnectError", event["disconnectReason"] )
        else:
            insertToDB(device_id, timestamp, "disconnected")
    else:
        insertToDB(device_id, timestamp, "connected")
    
    
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Finito')
    }
