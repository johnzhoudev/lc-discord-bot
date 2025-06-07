FROM python:3.13-alpine

WORKDIR /usr/src/lc_discord_bot

# Install packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src src

ENV BOT_CHANNEL_ID=1329240405476118659
ENV MAIN_CHANNEL_ID=1174483814081376436
ENV TEXT_JSON_FILE=text.json

CMD ["python", "-m", "src.bot"]