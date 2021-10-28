import json
from gql import gql, Client
import os
from gql.transport.requests import RequestsHTTPTransport
from aws_cdk import (
    core
)

class Mutation(core.Construct):
    def mutation(input):
        client = get_client()
        query = """
            mutation LambdaDeviceInfoTable($input: UpdateDeviceInfoTableInput!) {
                LambdaDeviceInfoTable(input: $input) {
                IsConnected
                IsOccupied
                PartitionKey
                SensorID
                SortKey
            }
            }
        """
        resp = client.execute(gql(query),
                            variable_values=json.dumps({"input": input}))

    def handler(event, context):

        headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": os.environ['API_KEY']
        }

        transport = RequestsHTTPTransport(
        url=os.environ['ENDPOINT'],
        use_json=True,
        headers=headers
        )
        client = Client(transport=transport,
                        fetch_schema_from_transport=True)

        newitem = {}
        for record in event['Records']:
            if record['eventName'] == 'MODIFY':
                for k1, v1 in record["dynamodb"]["NewImage"]:
                    for k2, v2 in v1:
                        newitem[k1] = v2
        
        #try:
        #    mutation(newitem)
        #except Exception as e:
        #    print(e)


