import json
import boto3
from boto3.dynamodb.conditions import Key
import os
import botocore
from botocore.vendored import requests
from datetime import datetime


########
#
# Gestice l'interazione con il bot telegram.
# In particolare, quando viene richiesto lo stato del dispositivo,
# va a leggere lo stato salvato in DynamoDb, e inoltre pubblica un messaggio al topic personale del dispotivo
# per triggerare il meccanismo di richiesta/risposta per monitorare lo stato di funzionamento del dispositivo
#
def parseTelegramCommand(textMessage):
    wordList = textMessage.split()
    
    parsedArgument = {}
    if "/start" in wordList:
        parsedArgument["start"] = True
    if "/setUser" in wordList:
        user = wordList[wordList.index('/setUser') + 1]
        parsedArgument["user_id"] = user
    
    if '/toggleAlert' in wordList:
        if wordList[wordList.index('/toggleAlert') + 2] == "Off":
            toogleAlert = False
            parsedArgument["toogleAlert"] = False
            user = wordList[wordList.index('/toggleAlert') + 1]
            parsedArgument["user"] = user
        elif wordList[wordList.index('/toggleAlert') + 2] == "On":
            toogleAlert = True
            parsedArgument["toogleAlert"] = True
            user = wordList[wordList.index('/toggleAlert') + 1]
            parsedArgument["user"] = user
            
    if '/infoDevice' in wordList:
        device = wordList[wordList.index('/infoDevice') + 1]
        parsedArgument["device_id_info"] = device
    
    return parsedArgument



def setUser(user, chat_id, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name="us-west-2")

    table = dynamodb.Table('Users')
    response = table.update_item(
        Key={
            'email': user
        },
        UpdateExpression="set chatID=:id, telegram=:t",
        ExpressionAttributeValues={
            ':id': chat_id,
            ':t': False
        },
        ReturnValues="UPDATED_NEW"
    )
    return response
    

    
def toogleAlertFunction(user, toggle, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name="us-west-2")
    
    table = dynamodb.Table('Users')
    response = table.update_item(
        Key={
            'email': user
        },
        UpdateExpression="set telegram=:t",
        ExpressionAttributeValues={
            ':t': toggle
        },
        ReturnValues="UPDATED_NEW"
    )
    return response
    

def getDeviceConnStatus(device_id, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name="us-west-2")

    table = dynamodb.Table('Devices')
    response = table.query(
        KeyConditionExpression=Key('device_id').eq(device_id)
    )
    
    return response['Items'][0]
    
def sendMessageToDeviceForInfo(device_id):
    client = boto3.client('iot-data')
    
    try:
        response = client.publish(
            topic="pcTelemetry/{}/infoRequest".format(device_id),
            qos=1,
            payload="Info request"
            )
        print(response)
        
    except botocore.exceptions.ClientError as error:
        print("Errore rilevato: ", error)


def lambda_handler(event, context):
    

    print(event)
    
    telegram_msg = event['message']['text']
    chat_id = event['message']['chat']['id']
    parsedMessage = parseTelegramCommand(event['message']['text'])
    
    if("start") in parsedMessage:
        telegram_msg = """Benvenuto nel bot di alert.
        Digita /setUser seguita dal tuo username per accoppiare il tuo account telegram al tuo account di telemetria
        Digita /toggleAlert seguito da 'On' oppure 'Off' per abilitare o disabilitare gli alert"""
        
    if "user_id" in parsedMessage:
        setUser(parsedMessage["user_id"], chat_id)
        telegram_msg = "Nome utente: " + str(parsedMessage["user_id"]) + "\nAlert disattivati. Per attivarli digita \"toggleAlert " + str(parsedMessage["user_id"]) + " On"
    if "toogleAlert" in parsedMessage:
        toogleAlertFunction(parsedMessage["user"], parsedMessage["toogleAlert"])
        telegram_msg = "Alert = " + str(parsedMessage["toogleAlert"])
        
    if "device_id_info" in parsedMessage:
        device_id = parsedMessage["device_id_info"]
        connStatus = getDeviceConnStatus(parsedMessage["device_id_info"])
        timestamp = int(connStatus["con_status_timestamp"]/1000)
        if(connStatus["connection_status"] == "disconnectError"):
            telegram_msg = "Il dispositivo si è disconnesso in maniera anomala.\nError code: " + connStatus["errorCode"] + "\nTimestamp disconnessione: " \
                            + str(datetime.fromtimestamp(timestamp))
        elif(connStatus["connection_status"] == "disconnected"):
            telegram_msg = "Il dispositivo è disconnesso\nTimestamp disconnessione: " \
                            + str(datetime.fromtimestamp(timestamp))
        elif(connStatus["connection_status"] == "connected"):
            telegram_msg = "Il dispositivo è connesso"
            sendMessageToDeviceForInfo(device_id)
        else:
            telegram_msg = "Nessuna info sullo stato della connessione del dispositivo"
        
        
    
    
    telegram_token = os.environ['TELEGRAM_BOT_TOKEN']
    
    api_url = f"https://api.telegram.org/bot{telegram_token}/"
    
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
