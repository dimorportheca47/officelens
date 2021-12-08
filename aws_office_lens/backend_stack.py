from aws_cdk import aws_appsync as appsync
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_iam as Policy
from aws_cdk import aws_iot as iot
from aws_cdk import aws_iotevents as iotevents
from aws_cdk import aws_iot_actions as actions
from aws_cdk import aws_kinesis as kinesis
from aws_cdk import aws_lambda as _lambda
from aws_cdk import core as cdk
# Lambda function triggered by DDB stream 
from stack import ( MutationStack, PutItemStack )

with open("./schema.txt") as f:
    definition = f.read()

with open("./query_DeviceTable_Resolver.txt") as f:
    query_DeviceTable_Resolver = f.read()


class BackendStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        iot_certificate_arn = self.node.try_get_context("iot_certificate_arn")

        graphql_api = appsync.CfnGraphQLApi(
            self,'graphqlApi',
            name="graphqlapi",
            authentication_type="API_KEY"
        )

        api_key = appsync.CfnApiKey(
            self, 'MutationKey',
            api_id=graphql_api.attr_api_id
        )

        self.graphql_api = graphql_api
        self.api_key = api_key

        cdk.CfnOutput(
            self,'EndPoint',
            description='REACT_APP_ENDPOINT',
            value=graphql_api.attr_graph_ql_url,
        )

        cdk.CfnOutput(
            self,'ApiKey',
            description='REACT_APP_API_KEY',
            value=api_key.attr_api_key,
        )

        device_table = ddb.Table(
            self, 'DeviceTable',
            table_name="DeviceTable",
            partition_key={'name':'PartitionKey', 'type': ddb.AttributeType.STRING},
            sort_key={'name':'SortKey', 'type': ddb.AttributeType.STRING},
            stream=ddb.StreamViewType.NEW_IMAGE,
            removal_policy=cdk.RemovalPolicy('DESTROY')
        )

        mutationTriggerdByDDBS = MutationStack(
            self, 'mutationTriggerdByDDBS',
            endpoint=graphql_api.attr_graph_ql_url,
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

        streamtoDeviceTable = kinesis.Stream(
            self, "streamtoDeviceTable",
            shard_count=1,
        )

        putItemToDeviceTable = PutItemStack(
            self, 'putItemToDeviceTable',
            table=device_table,
            partition=device_table.schema().partition_key.name,
            sort=device_table.schema().sort_key.name,
            stream=streamtoDeviceTable
        )

        # kinesisにアクセスするためのIAM Roleを設定する
        IoTRuleAccessKinesisStreamIamRole = iam.Role(
            self, 'IoTRuleAccessKinesisStreamIamRole',
            assumed_by=iam.ServicePrincipal('iot.amazonaws.com')
        )
        # iot rule からkinesis streamsにデータを投げるためのポリシーを作成する
        IoTKinesisPutRecordPolicy = iam.Policy(
            self, 
            "aws-iot-role-kinesisPutRecord_policy_{}".format(construct_id),
            statements=[iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["kinesis:PutRecord"],
                resources=[streamtoDeviceTable.stream_arn]
                )
                ]
            )
        # 上で作成したポリシーをロールにアタッチする
        IoTRuleAccessKinesisStreamIamRole.add_managed_policy(
            IoTKinesisPutRecordPolicy
            )

        IoTRuleIAMRoleARN = IoTRuleAccessKinesisStreamIamRole.role_arn
        
        topic_rule = iot.CfnTopicRule(
            self, "DeviceDataRule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        kinesis=iot.CfnTopicRule.KinesisActionProperty(
                            role_arn=IoTRuleIAMRoleARN,
                            stream_name=streamtoDeviceTable.stream_name,
                            partition_key="${newuuid()}",
                            )
                    )
                ],
                sql="SELECT *, topic(2) AS Building, topic(3) AS Floor, topic(4) AS SeatID FROM 'data/#' ",
            )
        )
        # thingを定義
        thing_name="RasberryPi2"
        cfn_thing = iot.CfnThing(self, "OfficeMonitoringThing", thing_name=thing_name)
        policy_document = {
            "Version": '2012-10-17',
            "Statement": [
              {
                "Effect": 'Allow',
                "Action": 'iot:*',
                "Resource": '*',
              },
            ],
          }
        # policyを定義
        policy_name = "RasberryPi-Policy"
        cfn_iot_policy = iot.CfnPolicy(self, "IoTPolicy",
            policy_document=policy_document,
            policy_name = policy_name)
        # policyを証明書に紐付け
        cfn_policy_principal_attachment = iot.CfnPolicyPrincipalAttachment(self, "MyCfnPolicyPrincipalAttachment",
            policy_name=policy_name,
            principal=iot_certificate_arn
        )
        cfn_policy_principal_attachment.add_depends_on(cfn_iot_policy)
        # 証明書とthingを紐付け
        cfn_thing_principal_attachment = iot.CfnThingPrincipalAttachment(self, "MyCfnThingPrincipalAttachment",
            principal=iot_certificate_arn,
            thing_name=thing_name
        )
        cfn_thing_principal_attachment.add_depends_on(cfn_thing)
        
        # IoTEventから呼び出されるlambdaのロール
        upsertConnectionStatusFunctionIamRole = iam.Role(
            self, 'upsertConnectionStatusFunctionIamRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )
        upsertConnectionStatusFunctionIamRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'))
        upsertConnectionStatusFunctionIamRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSIoTEventsReadOnlyAccess'))
        # IoTEventから発火されるdynamodbの項目をdisconectedに書き換えるlambdaを定義する
        upsertConnectionStatusFunction = _lambda.Function(
            self,
            id="upsertConnectionStatusFunction",
            code=_lambda.Code.asset('lambda'),
            handler="upsertConnectionStatus.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            role=upsertConnectionStatusFunctionIamRole
            )

        #ioteventsのinputを定義
        cfn_input = iotevents.CfnInput(self, "MyCfnInput",
            input_definition=iotevents.CfnInput.InputDefinitionProperty(
                attributes=[
                    iotevents.CfnInput.AttributeProperty(json_path="eventType"),
                    iotevents.CfnInput.AttributeProperty(json_path="ipAddress"),
                    iotevents.CfnInput.AttributeProperty(json_path="clientId"),
                    ]
            ),
            input_name="device_checker_input",
            
        )

        # iot eventsのdetector modelを定義
        detector_model_definition = iotevents.CfnDetectorModel.DetectorModelDefinitionProperty(
            initial_state_name="Connnected",
            states=[iotevents.CfnDetectorModel.StateProperty(
                    state_name="Connnected",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[],
                        transition_events=[
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="to_disconnected",
                                condition="$input.device_checker_input.eventType == \"disconnected\"",
                                actions=[],
                                next_state="Disconnected"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="init",
                                condition="$input.device_checker_input.eventType == \"connected\"",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        set_variable=iotevents.CfnDetectorModel.SetVariableProperty(
                                            variable_name="ipAddress",
                                            value="$input.device_checker_input.ipAddress"
                                        )
                                    ),
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        lambda_=iotevents.CfnDetectorModel.LambdaProperty(
                                            function_arn=upsertConnectionStatusFunction.function_arn,
                                            payload=iotevents.CfnDetectorModel.PayloadProperty(
                                                content_expression="'{\n  \"clientId\": \"${$input.device_checker_input.clientId}\",\n  \"isConnected\": \"${$input.device_checker_input.eventType == \"connected\"}\"\n}'",
                                                type="JSON"
                                            )
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[]
                    )
                ),
                iotevents.CfnDetectorModel.StateProperty(
                    state_name="Disconnected",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[],
                        transition_events=[
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="to_connected",
                                condition="$input.device_checker_input.eventType == \"connected\"",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        clear_timer=iotevents.CfnDetectorModel.ClearTimerProperty(
                                            timer_name="alert_timer"
                                        )
                                    )
                                ],
                                next_state="Connnected"
                            ),
                            iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="to_alert",
                                condition="timeout(\"alert_timer\")",
                                actions=[],
                                next_state="alart"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="init",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        set_timer=iotevents.CfnDetectorModel.SetTimerProperty(
                                            timer_name="alert_timer",
                                            seconds=60
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[]
                    )
                ),
                iotevents.CfnDetectorModel.StateProperty(
                    state_name="alart",
                    on_input=iotevents.CfnDetectorModel.OnInputProperty(
                        events=[],
                        transition_events=[iotevents.CfnDetectorModel.TransitionEventProperty(
                                event_name="to_connected",
                                condition="$input.device_checker_input.eventType == \"connected\"",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        clear_timer=iotevents.CfnDetectorModel.ClearTimerProperty(
                                            timer_name="alert_timer"
                                        )
                                    )
                                ],
                                next_state="Connnected"
                            )
                        ]
                    ),
                    on_enter=iotevents.CfnDetectorModel.OnEnterProperty(
                        events=[
                            iotevents.CfnDetectorModel.EventProperty(
                                event_name="init",
                                condition="true",
                                actions=[
                                    iotevents.CfnDetectorModel.ActionProperty(
                                        lambda_=iotevents.CfnDetectorModel.LambdaProperty(
                                            function_arn=upsertConnectionStatusFunction.function_arn,
                                            payload=iotevents.CfnDetectorModel.PayloadProperty(
                                                content_expression="'{\n  \"clientId\": \"${$input.device_checker_input.clientId}\",\n  \"isConnected\": \"${$input.device_checker_input.eventType == \"connected\"}\"\n}'",
                                                type="JSON"
                                            )
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                    on_exit=iotevents.CfnDetectorModel.OnExitProperty(
                        events=[]
                    )
                )
            ],
        )
        
        # IoTEvents様のroleを立てる
        IoTEventIamRole = iam.Role(
            self, 'IoTEventIamRole',
            assumed_by=iam.ServicePrincipal('iotevents.amazonaws.com')
        )
        # iotEventのポリシーを作成する
        IoTEventPolicy = iam.Policy(
            self, 
            "IotEventsConsoleActionsExecutionRole-{}".format(construct_id),
            statements=[
                iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["iot:Publish"],
                resources=["arn:aws:iot:ap-northeast-1:{}:topic/*".format(self.account)]
                ),
                iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=["arn:aws:iot:ap-northeast-1:{}:function:*".format(self.account)]
                ),
                iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["iotevents:BatchPutMessage"],
                resources=["arn:aws:iot:ap-northeast-1:{}:input/*".format(self.account)]
                ),
                iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sso-directory:DescribeUser"],
                resources=["*"]
                ),
                ]
            )
        # 上で作成したポリシーをロールにアタッチする
        IoTEventIamRole.add_managed_policy(
            IoTEventPolicy
            )

        IoTEventIAMRoleARN = IoTEventIamRole.role_arn
        #IoTEventsをたてる
        cfn_detector_model = iotevents.CfnDetectorModel(self, "CfnDetectorModel",
            detector_model_definition=detector_model_definition,
            detector_model_name="device_connection_checker",
            role_arn=IoTEventIAMRoleARN,
            evaluation_method="BATCH"
            )
        # IoTRuleforIoTEvents様のroleを立てる
        IoTRuleforIoTEventIamRole = iam.Role(
            self, 'IoTRuleforIoTEventIamRole',
            assumed_by=iam.ServicePrincipal('iot.amazonaws.com')
        )
        # IoTRuleforIoTEventsのポリシーを作成する
        IoTRuleforIoTEventPolicy = iam.Policy(
            self, 
            "IoTRuleforIoTEventPolicy_{}".format(construct_id),
            statements=[iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["iotevents:BatchPutMessage"],
                resources=[streamtoDeviceTable.stream_arn]
                )]
            )
        # 上で作成したポリシーをロールにアタッチする
        IoTRuleforIoTEventIamRole.add_managed_policy(
            IoTRuleforIoTEventPolicy
            )

        IoTRuleforIoTEventIAMRoleARN = IoTRuleforIoTEventIamRole.role_arn
        # IoTEvents様のtopicrule
        IoTEventsRule = iot.CfnTopicRule(
            self, "IoTEventsRule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        iot_events=iot.CfnTopicRule.IotEventsActionProperty(
                            input_name="device_checker_input",
                            role_arn=IoTRuleforIoTEventIAMRoleARN,
                            batch_mode=False,
                            )
                    )
                ],
                sql="SELECT clientId as clientId, eventType as eventType, ipAddress as ipAddress FROM '$aws/events/presence/#'",
            )
        )
        
        
