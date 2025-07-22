import boto3


def get_from_ssm(id: str):
    ssm = boto3.client("ssm", region_name="us-east-1")
    param = ssm.get_parameter(Name=f"/lc-discord-bot/{id}", WithDecryption=True)
    return param["Parameter"]["Value"]
