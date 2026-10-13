"""
Libero - AWS CDK App
"""

import os
import aws_cdk as cdk

from stacks.data_stack import DataStack
from stacks.compute_stack import ComputeStack
from stacks.api_stack import ApiStack
from stacks.iot_stack import IoTStack
from stacks.notification_stack import NotificationStack

app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "us-east-1")
)

# Stack 1: Dados (DynamoDB, Timestream, S3)
data_stack = DataStack(app, "LiberoDataStack", env=env)

# Stack 2: Computação (Lambda, Bedrock)
compute_stack = ComputeStack(
    app, "LiberoComputeStack",
    data_stack=data_stack,
    env=env
)

# Stack 3: API (API Gateway, MCP)
api_stack = ApiStack(
    app, "LiberoApiStack",
    compute_stack=compute_stack,
    env=env
)

# Stack 4: IoT (dispositivos edge)
iot_stack = IoTStack(app, "LiberoIoTStack", env=env)

# Stack 5: Notificação (SNS, SES)
notification_stack = NotificationStack(app, "LiberoNotificationStack", env=env)

app.synth()
