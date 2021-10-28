# AWS Office Lens の使い方

## 目次

* 参考
* 概要
* AWS CDK のCLIのインストール
* AWS CDK プロジェクトの作成
* 仮想環境のアクティブ化
* パッケージの追加
* Backend Stackの作成
* Web アプリケーションのビルド
* Frontend Stackの作成
* ブラウザで確認
* お掃除
* その他

## 参考

https://docs.aws.amazon.com/cdk/api/latest/python/
https://dev.classmethod.jp/articles/cloudfront-origin-access-identity-to-restrict-access-to-s3-bucket-in-aws-cdk/
https://summit-online-japan-cdk.workshop.aws/15-prerequisites/600-python.html
https://dev.classmethod.jp/articles/aws-cdk-deploy-react/

## 概要

[Image: スクリーンショット 0003-10-08 13.46.52.png]
## AWS CDK のCLIのインストール

```
npm install -g aws-cdk
```

## プロジェクトの作成 or AWS Office Lens をCodeCommit から持ってくる

```
# 作業ログ
mkdir aws-office-lens
cd aws-office-lens
cdk init app --language=python

# clone
`git clone https://git-codecommit.ap-northeast-1.amazonaws.com/v1/repos/AWS-Office-Lens`
```

## 仮想環境のアクティブ化

```
source .venv/bin/activate
```

## パッケージの追加（足りないのあったらその都度入れてくださいませ）

```
pip install aws-cdk.aws-appsync aws-cdk.aws-cloudfront aws-cdk.aws-s3 aws-cdk.aws-s3-deployment（現状のディレクトリ構成はこんな感じ）
```

```
`.``venv ``❯`` tree ``.`` ``-``I node_modules -L 2 （一部）省略
├── README.md
├── app.py
├── aws_office_lens
│   ├── __init__.py
│   ├── backend_stack.py # Raspi から Appsync 
│   └── frontend_stack.py # S3, Cloudfront
├── cdk.json
├── cdk.out
├── lambda
│   ├── mutation.py # DDB Stream をトリガーにMutationするやつ
│   └── putitem.py # Kinesis Stream で来たやつをDDB に書き込むやつ
├── query_DeviceTable_Resolver.txt # Appsyc のリゾルバ
├── requirements.txt
├── schema.txt # Appsync のスキーマ
├── setup.py
├── source.bat
├── stack.py # front or backend で使ってるstack
└── web
    ├── README.md
    ├── build # cloudfront にデプロイされるファイル
    ├── package-lock.json
    ├── package.json
    ├── public
    ├── src
    ├── tsconfig.json
    └── yarn.lock`
```

## BackendStack （Raspi からAppsync まで）の作成

とりあえず、backendstack をデプロイ

```
初めてのデプロイの場合は cdk bootstrap
差分を確認したいなら cdk diff {StackName}
cdk deploy BackendStack
```

デプロイが初回なら数分かかるかなーー
[Image: スクリーンショット 2021-10-28 21.31.42.png]デプロイが終わるとCfnOutput で作成したAppsync のAPI_KEY とENDPOINT を出力されるのでメモっとく

## Web アプリケーションのビルド

ビルドする前に環境変数にさっきメモしたやつをぶち込みましょう

```
# web/.env
REACT_APP_API_KEY=da2-hnc62rbufjcgtm72buavridvhm
REACT_APP_ENDPOINT=https://vyi6bkwcu5eqlo6zhwwcphd5fu.appsync-api.ap-northeast-1.amazonaws.com/graphql
```

これでビルド出来る準備が出来なのでビルドしましょう

```
# web の配下まで移動 & ビルド
cd ./../web
yarn build
```

## FrontendStack （S3 + CloudFront）の作成

```
cd ./../aws_office_lens
cdk deploy FrontendStack
```

## ブラウザで確認

確認できたらおしまい。おつかれさまでした。
[Image: スクリーンショット 2021-10-28 21.53.59.png]
## 環境のお掃除

```
cdk deｓtroy FrontendStack
cdk deｓtroy BackendStack
```

## コードの解説 etc

### Appsync APIの作成

* aws_office_lens_stack.pyに黄色の箇所を追加
    * 作成したAppsyncに用いるためのAPI KEYも作成する必要あり

```
from aws_cdk import (
    core as cdk,
    aws_lambda as _lambda,
    aws_cloudfront as cloudfront,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_appsync as appsync,
    )


class AwsOfficeLensStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        graphql_api = appsync.CfnGraphQLApi(
            self,'graphqlApi',
            name="graphql-api",
            authentication_type="API_KEY"
        )
        
         api_key = appsync.CfnApiKey(
            self, 'Mutation-key',
            api_id=graphql_api.attr_api_id
        )

```

* （リゾルバが一切ないので書く必要がある）
    * データソース
        * Device(DynamoDB
        * Mutation(ソースなし)
    * スキーマ
        * 調査中...

### Lambdaの作成

* lambdaのコードをアップロードするディレクトリの作成とPythonモジュールのGraphQLのインストール

```
mkdir lamda
cd lambda
touch mutation.py
```

* JSで元々書いていたのでそれをPythonに書き換える中....
* Stackに追加
    * EndpointはAppsyncになるため引数に取る必要あり
    * keyも同様に作成ズムのAPI KEYを参照

```
class BackendStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        graphql_api = appsync.CfnGraphQLApi(
            self,'graphqlApi',
            name="graphql-api",
            authentication_type="API_KEY"
        )

        api_key = appsync.CfnApiKey(
            self, 'Mutation-key',
            api_id=graphql_api.attr_api_id
        )

        ddbs_mutation = Mutation(
            self, 'DDBSMutation',
            endpoint = graphql_api.attr_graph_ql_url,
            key=api_key.attr_api_key
        )
```

### S3バケットの作成

* frontend_stack.pyに下記を追加

```
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
```

### CloudFrontの作成

* S3バケットのコードの下に以下を追加

```
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
```

### 実際にReact アプリケーションをS3にデプロイする

```
        s3deploy.BucketDeployment(
            self, 'WebsiteDeploy',
            sources=[s3deploy.Source.asset('./web/build')],
            destination_bucket=website_Bucket,
            distribution=website_Distribution,
            distribution_paths=['/*']
        )
```


