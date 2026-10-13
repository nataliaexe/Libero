"""
Libero - Stack de Dados
DynamoDB, Timestream, S3
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_timestream as timestream,
    aws_s3 as s3,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct


class DataStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # DynamoDB - Estado
        self.state_table = dynamodb.Table(
            self, "LiberoState",
            table_name="libero-state",
            partition_key=dynamodb.Attribute(
                name="idoso_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )
        
        # Timestream - Séries temporais
        self.timestream_db = timestream.CfnDatabase(
            self, "LiberoTimestreamDB",
            database_name="libero"
        )
        
        self.timestream_table = timestream.CfnTable(
            self, "LiberoTimestreamTable",
            database_name="libero",
            table_name="events",
            retention_properties=timestream.CfnTable.RetentionPropertiesProperty(
                memory_store_retention_period_in_hours=24,
                magnetic_store_retention_period_in_days=365
            )
        )
        self.timestream_table.add_dependency(self.timestream_db)
        
        # S3 - Dados brutos
        self.data_bucket = s3.Bucket(
            self, "LiberoData",
            bucket_name=f"libero-data-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="audio-expire",
                    prefix="audio/",
                    expiration=None,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=None
                        )
                    ]
                )
            ]
        )
        
        # Outputs
        CfnOutput(self, "StateTableName", value=self.state_table.table_name)
        CfnOutput(self, "TimestreamDatabase", value=self.timestream_db.database_name)
        CfnOutput(self, "TimestreamTable", value=self.timestream_table.table_name)
        CfnOutput(self, "DataBucketName", value=self.data_bucket.bucket_name)
