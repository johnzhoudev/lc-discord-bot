FROM python:3.13-alpine

WORKDIR /usr/src/lc_discord_bot

# Install packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.bot"]