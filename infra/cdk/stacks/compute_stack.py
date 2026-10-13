"""
Libero - Stack de Computação
Lambdas + Bedrock
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    Duration,
    CfnOutput
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(self, scope: Construct, id: str, data_stack, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Role para o Bedrock
        bedrock_role = iam.Role(
            self, "LiberoBedrockRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonBedrockFullAccess"
                )
            ]
        )
        
        # Permissões para dados
        data_stack.state_table.grant_read_write_data(bedrock_role)
        data_stack.data_bucket.grant_read_write(bedrock_role)
        
        # Lambda do Orquestrador
        self.orchestrator_fn = lambda_.Function(
            self, "LiberoOrchestrator",
            function_name="libero-orchestrator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="cloud.agents.orchestrator.lambda_handler",
            code=lambda_.Code.from_asset("../../"),
            timeout=Duration.seconds(30),
            memory_size=512,
            role=bedrock_role,
            environment={
                "DYNAMODB_TABLE": data_stack.state_table.table_name,
                "S3_BUCKET": data_stack.data_bucket.bucket_name,
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
            }
        )
        
        CfnOutput(self, "OrchestratorFnArn", value=self.orchestrator_fn.function_arn)
