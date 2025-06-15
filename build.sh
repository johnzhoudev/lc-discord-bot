docker build -t jzhou/discord-lc-bot .
docker tag jzhou/discord-lc-bot 273354659414.dkr.ecr.us-east-1.amazonaws.com/lc-discord-bot:latest
# powershell 'docker login --username AWS -p $(aws ecr get-login-password --region us-east-1) 273354659414.dkr.ecr.us-east-1.amazonaws.com'
docker push 273354659414.dkr.ecr.us-east-1.amazonaws.com/lc-discord-bot:latest