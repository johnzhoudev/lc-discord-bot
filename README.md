# Leetcode discord bot

## Setup

### Windows
1. Install `python 3.13.2` (using pyenv, or any python verison manager)
2. Run `python -m venv ./.venv/lc-discord-bot`
3. Run `./.venv/lc-discord-bot/Scripts/Activate.ps1` on windows
4. ... TBD

### Macbook
1. Run `pyenv virtualenv 3.13.2 lc-discord-bot`
2. Run `pyenv activate lc-discord-bot`


## Development

Run with `python -m src.bot` from root directory. Need to do this so that the src module is treated correctly.

### Terraform
`terraform apply -var-file="terraform.tfvars"`

### Running tests
In the root directory, run
```
pytest
```

## Deployment

### Docker build command
`docker build -t jzhou/discord-lc-bot .`

### Docker tag command
`docker tag jzhou/discord-lc-bot 273354659414.dkr.ecr.us-east-1.amazonaws.com/lc-discord-bot:latest`

### Docker push command

First you must login to the ECR repo:

`powershell 'docker login --username AWS -p $(aws ecr get-login-password --region us-east-1) 273354659414.dkr.ecr.us-east-1.amazonaws.com'`

Then push the image:

`docker push 273354659414.dkr.ecr.us-east-1.amazonaws.com/lc-discord-bot:latest`