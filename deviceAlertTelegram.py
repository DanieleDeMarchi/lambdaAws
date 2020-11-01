import json
import boto3
from boto3.dynamodb.conditions import Key
import os
from botocore.vendored import requests

#################
#
# funzione triggerata quando livello batteria basso. Invia alert tramite bot telegram
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
    
    dynamodb = boto3.resource('dynamodb', region_name="us-west-2")

    user = findDeviceOwner(device_id, dynamodb)
    chat_id = findChatId(user, dynamodb)
    
    print(chat_id)
    
    telegram_token = os.environ['TELEGRAM_BOT_TOKEN']
    api_url = f"https://api.telegram.org/bot{telegram_token}/"
    
    telegram_msg = "Batteria quasi scarica\n" + "Device: " + device_id + "\nMinuti rimanenti: " \
                        + str(event["min_left"]) + "\nPercentuale rimanente: " + str(event["percent"])
    
    
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


    
