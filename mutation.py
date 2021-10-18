from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_lambda_event_sources as source,
)
from aws_cdk.aws_dynamodb import ITable

class Mutation(core.Construct):
    @property
    def handler(self):
        return self._handler

    def __init__(self, scope: core.Construct, id: str, endpoint: str, key: str, table: ITable, **kwargs):
        super().__init__(scope, id, **kwargs)

        self._handler = _lambda.Function(
            self, 'MutationHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler='mutation.handler',
            code=_lambda.Code.asset('lambda'),
            environment={
                'ENDPOINT':  endpoint,
                'API_KEY': key
            }
        )

        self._handler.add_event_source(
            source.DynamoEventSource(
                table,
                starting_position=_lambda.StartingPosition.LATEST
        ))

