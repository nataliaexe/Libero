"""
Libero - Stack de API
API Gateway + MCP Server
"""

from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    CfnOutput
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, compute_stack, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # API Gateway
        self.api = apigw.RestApi(
            self, "LiberoApi",
            rest_api_name="libero-api",
            description="API do Libero"
        )
        
        # Recurso /mcp
        mcp_resource = self.api.root.add_resource("mcp")
        
        # POST /mcp → Lambda do orquestrador
        mcp_resource.add_method(
            "POST",
            apigw.LambdaIntegration(compute_stack.orchestrator_fn)
        )
        
        # GET /health
        health_resource = self.api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigw.MockIntegration(
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '{"status": "ok"}'
                    }
                }],
                passthrough_behavior=apigw.PassthroughBehavior.NEVER,
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            )
        )
        
        CfnOutput(self, "ApiUrl", value=self.api.url)
