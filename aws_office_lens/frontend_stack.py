from aws_cdk import (
    core as cdk,
    aws_cloudfront as cloudfront,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam 
    )

from mutation import Mutation

class FrontendStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        website_Bucket = s3.Bucket(
            self, 'WebsiteBucket',
            website_error_document='index.html',
            website_index_document='index.html',
            block_public_access=
                s3.BlockPublicAccess(
                    block_public_acls=True,
                    block_public_policy=True,
                    ignore_public_acls=True,
                    restrict_public_buckets=True
                ),
            versioned=False

        )

        website_identity = cloudfront.OriginAccessIdentity(
            self, 'WebsiteIdentity'
        )

        website_Bucket_Policy = iam.PolicyStatement(
            actions=['s3:GetObject'],
            effect=iam.Effect.ALLOW,
            principals=[website_identity.grant_principal],
            resources=[website_Bucket.bucket_arn + '/*']
        )

        website_Bucket.add_to_resource_policy(website_Bucket_Policy)

        website_Distribution = cloudfront.CloudFrontWebDistribution(
            self, 'WebsiteDistribution',
            error_configurations=[
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_caching_min_ttl=300,
                    error_code=403,
                    response_code=200,
                    response_page_path='/index.html'
            ),
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                error_caching_min_ttl=300,
                    error_code=404,
                    response_code=200,
                    response_page_path='/index.html'

            ),
            ],
            origin_configs=[cloudfront.SourceConfiguration(
                s3_origin_source=cloudfront.S3OriginConfig(
                    s3_bucket_source=website_Bucket,
                    origin_access_identity=website_identity,
                ),
                behaviors=[cloudfront.Behavior(is_default_behavior=True)]
            )
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
        )

        s3deploy.BucketDeployment(
            self, 'WebsiteDeploy',
            sources=[s3deploy.Source.asset('./web/build')],
            destination_bucket=website_Bucket,
            distribution=website_Distribution,
            distribution_paths=['/*']
        )