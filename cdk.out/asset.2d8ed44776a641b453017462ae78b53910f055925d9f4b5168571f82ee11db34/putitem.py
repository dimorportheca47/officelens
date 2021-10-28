from __future__ import print_function
import base64
import boto3
import json
import os
import traceback

#-----Dynamo Info change here------
TABLE_NAME = os.environ['TABLE_NAME']
DDB_PRIMARY_KEY = os.environ['PARTITION_KEY']
DDB_SORT_KEY = os.environ['SORT_KEY']

#-----Dynamo Info change here------
dynamodb = boto3.resource('dynamodb')
table  = dynamodb.Table(TABLE_NAME)
def checkItem(str_data):
    try:
        #String to Json object
        print("CheckItem data: {}".format(str_data))
        json_data = json.loads(str_data)
        # adjust your data format
        atribute = json_data["Building"] +"_" +  json_data["Floor"]
        json_data['Building#Floor'] = atribute
        resDict = {
            DDB_PRIMARY_KEY:json_data['Building#Floor'],
            DDB_SORT_KEY:json_data['SeatID'],
            "SensorID": json_data['SensorID'],
            "IsOccupied": json_data['IsOccupied'],
            "IsConnected": True
        }
        print("resDict:{}".format(resDict))
        return resDict

    except Exception as e:
        print(traceback.format_exc())
        return None

def writeItemInfo(datas):
    ItemInfoDictList = []
    try:
        for data in datas:
            itemDict = checkItem(data)
            if None != itemDict:
                ItemInfoDictList.append(itemDict)
            # if data does not have key info, just pass
            else:
                print("Error data found:{}".format(data))
                pass

    except Exception as e:
        print(traceback.format_exc())
        print("Error on writeItemInfo")

    return ItemInfoDictList

def DynamoBulkPut(datas):
    try:
        putItemDictList = writeItemInfo(datas)
        with table.batch_writer(overwrite_by_pkeys=[DDB_PRIMARY_KEY, DDB_SORT_KEY]) as batch:
            for putItemDict in putItemDictList:
                batch.put_item(Item = putItemDict)
        return

    except Exception as e:
        print("Error on DynamoBulkPut()")
        raise e

def decodeKinesisData(dataList):
    decodedList = []
    try:
        for data in dataList:
            payload =  base64.b64decode(data['kinesis']['data'])
            print("payload={}".format(payload))
            decodedList.append(payload)

        return decodedList

    except Exception as e:
        print("Error on decodeKinesisData()")
        raise e

def handler(event, context):
    try:
        encodeKinesisList = event['Records']
        decodedKinesisList = decodeKinesisData(encodeKinesisList)
        # Dynamo Put
        if len(decodedKinesisList):
            DynamoBulkPut(decodedKinesisList)
        else:
            print("there is no valid data in Kinesis stream, all data passed")
        return

    except Exception as e:
        print(traceback.format_exc())
        raise e