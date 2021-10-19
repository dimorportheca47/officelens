from aws_cdk import (
    core as cdk,
    aws_appsync as appsync,
    aws_dynamodb as ddb,
    aws_iam as iam
    )

from mutation import Mutation
with open("./schema.txt") as f:
    definition = f.read()

with open("./query_DeviceTable_Resolver.txt") as f:
    query_DeviceTable_Resolver = f.read()

class BackendStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        graphql_api = appsync.CfnGraphQLApi(
            self,'graphqlApi',
            name="graphqlapi",
            authentication_type="API_KEY"
        )

        api_key = appsync.CfnApiKey(
            self, 'MutationKey',
            api_id=graphql_api.attr_api_id
        )

        cdk.CfnOutput(
            self,'EndPoint',
            description='Appsync EndPoint: ',
            value=graphql_api.attr_graph_ql_url
        )

        cdk.CfnOutput(
            self,'ApiKey',
            description='Appsync ApiKey: ',
            value=api_key.attr_api_key
        )

        device_table = ddb.Table(
            self, 'DeviceTable',
            table_name="DeviceTable",
            partition_key={'name':'PartitionKey', 'type': ddb.AttributeType.STRING},
            sort_key={'name':'SortKey', 'type': ddb.AttributeType.STRING},
            stream=ddb.StreamViewType.NEW_IMAGE,
            removal_policy=cdk.RemovalPolicy('DESTROY')
        )

        ddbs_mutation = Mutation(
            self, 'DDBSMutation',
            endpoint = graphql_api.attr_graph_ql_url,
            key=api_key.attr_api_key,
            table=device_table
        )

        dataSourceIamRole = iam.Role(
            self, 'dataSourceIamRole',
            assumed_by=iam.ServicePrincipal('appsync.amazonaws.com')
        )

        dataSourceIamRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'))

        ddb_source = appsync.CfnDataSource(
            self, 'DDBSource',
            name='ddbsource',
            service_role_arn=dataSourceIamRole.role_arn,
            api_id=graphql_api.attr_api_id,
            type='AMAZON_DYNAMODB',
            dynamo_db_config=appsync.CfnDataSource.DynamoDBConfigProperty(
                table_name=device_table.table_name,
                aws_region=self.region
            )
        )

        none_source = appsync.CfnDataSource(
            self, 'NONESource',
            name='nonesource',
            api_id=graphql_api.attr_api_id,
            type='NONE'
        )  

        schema = appsync.CfnGraphQLSchema(
            self,"GraphQLSchema",
            api_id=graphql_api.attr_api_id,
            definition=definition
        )

        queryDeviceTableResolver = appsync.CfnResolver(
            self,"queryDeviceTableResolver",
            api_id=graphql_api.attr_api_id,
            type_name="Query",
            field_name='queryDeviceTable',
            data_source_name=ddb_source.name,
            request_mapping_template=query_DeviceTable_Resolver,
            response_mapping_template="$util.toJson($ctx.result)"
        )

        queryDeviceTableResolver.add_depends_on(schema)
        queryDeviceTableResolver.add_deletion_override("GraphQLSchema")

        mutationDeviceTableResolver = appsync.CfnResolver(
            self,"mutationDeviceTableResolver",
            api_id=graphql_api.attr_api_id,
            type_name="Mutation",
            field_name='MutationDeviceTable',
            data_source_name=none_source.name,
            request_mapping_template='{"version": "2017-02-28","payload": $util.toJson($ctx.args.input)}',
            response_mapping_template="$util.toJson($ctx.result)"
        )

        mutationDeviceTableResolver.add_depends_on(schema)
        mutationDeviceTableResolver.add_deletion_override("GraphQLSchema")