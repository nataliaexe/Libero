"""
Libero - Stack de Notificação
SNS para família
"""

from aws_cdk import (
    Stack,
    aws_sns as sns,
    CfnOutput
)
from constructs import Construct


class NotificationStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Tópico SNS para família
        self.family_topic = sns.Topic(
            self, "LiberoFamilyTopic",
            topic_name="libero-family-alerts",
            display_name="Libero - Alertas da Família"
        )
        
        CfnOutput(self, "FamilyTopicArn", value=self.family_topic.topic_arn)
