import json
import boto3
from boto3.dynamodb.conditions import Key
import os
from botocore.vendored import requests

################
# 
# Gestisce la risposta dello stato del dispositivo richiesta in precedenza tramite Telegram.
# Trova dispositivo e chat a cui inviare messaggio in DynamoDB
#


def findDeviceOwner(device_id, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name="us-west-2")

    table = dynamodb.Table('Devices')
    response = table.query(
        KeyConditionExpression=Key('device_id').eq(device_id)
    )
    
    print(response['Items'])
    return response['Items'][0]['owner']
    
    
def findChatId(user, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name="us-west-2")

    table = dynamodb.Table('Users')
    response = table.query(
        KeyConditionExpression=Key('email').eq(user)
    )
    
    print(response['Items'])
    return response['Items'][0]['chatID']
    
    

def lambda_handler(event, context):
    print(event)
    
    device_id = event['device_id']

    user = findDeviceOwner(device_id)
    chat_id = findChatId(user)
    
    print(chat_id)
    
    telegram_token = os.environ['TELEGRAM_BOT_TOKEN']
    api_url = f"https://api.telegram.org/bot{telegram_token}/"
    
    telegram_msg = event["responseMessage"]
    
    telegram_msg += "\nPer la dashboard di telemetria visita la pagina http://34.216.251.49:3000/"
    
    
    
    params = {'chat_id': chat_id, 'text': telegram_msg }
    res = requests.post(api_url + "sendMessage", data=params).json()
    
    
    if res["ok"]:
        return {
            'statusCode': 200,
            'body': res['result'],
        }
    else:
        print(res)
        return {
            'statusCode': 400,
            'body': res
        }
