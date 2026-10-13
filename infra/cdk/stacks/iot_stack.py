"""
Libero - Stack de IoT
Core IoT para dispositivos edge
"""

from aws_cdk import (
    Stack,
    aws_iot as iot,
    CfnOutput
)
from constructs import Construct


class IoTStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Thing para o dispositivo edge
        self.thing = iot.CfnThing(
            self, "LiberoEdgeThing",
            thing_name="libero-edge-01"
        )
        
        CfnOutput(self, "ThingName", value=self.thing.thing_name or "")
