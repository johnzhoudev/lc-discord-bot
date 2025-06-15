import boto3


def get_bot_token_from_ssm():
    ssm = boto3.client("ssm", region_name="us-east-1")
    param = ssm.get_parameter(Name="/lc-discord-bot/BOT_TOKEN", WithDecryption=True)
    return param["Parameter"]["Value"]
