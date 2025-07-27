FROM python:3.13-alpine

WORKDIR /usr/src/lc_discord_bot

# Setup time zone
# Install tzdata package (time zone database)
RUN apk add --no-cache tzdata

# Set the container timezone to Eastern Time
ENV TZ=America/New_York

# Copy timezone info for localtime
RUN cp /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src src

ENV BOT_CHANNEL_ID=1329240405476118659
ENV MAIN_CHANNEL_ID=1174483814081376436
ENV TEXT_JSON_FILE=text.json

CMD ["python", "-m", "src.bot"]