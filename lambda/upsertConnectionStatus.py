import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import os

#-----Dynamo 情報はここを変更------
TABLE_NAME = os.environ.get('TABLE_NAME', "default")
DDB_PRIMARY_KEY = "PartitionKey"
DDB_SORT_KEY = "SortKey"
#-----Dynamo 情報はここを変更------

dynamodb = boto3.resource('dynamodb')
table  = dynamodb.Table(TABLE_NAME)

# 条件なしアップサート
def upsert_dynamo(DPK, DSK, isConnectedFlag):
    option = {
        'Key': {DDB_PRIMARY_KEY: DPK, DDB_SORT_KEY: DSK},
        'UpdateExpression': 'set #IsConnected = :is_connected',
        'ExpressionAttributeNames': {
            '#IsConnected': 'IsConnected'
        },
        'ExpressionAttributeValues': {
            ':is_connected': isConnectedFlag
        }
    }
    table.update_item(**option)
    

def lambda_handler(event, context):
    # Global Secondaly IndexからPKとSKを取得
    print(f"[DEBUG: called] SensorID:{event['clientId']}")
    
    resp = table.query(
        IndexName="SensorIDGSI",
        KeyConditionExpression=Key('SensorID').eq(event['clientId']),
    )
    
    # 該当するフィールドのステータスを変更
    for r in resp["Items"]:
        print(f"[DEBUG: change] PK: {r[DDB_PRIMARY_KEY]}, iC: {event['isConnected']}")
        upsert_dynamo(r[DDB_PRIMARY_KEY], r[DDB_SORT_KEY], event['isConnected'] == 'true')
        
    print(" ########## ")