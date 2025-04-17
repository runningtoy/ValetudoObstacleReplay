FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev libfreetype6-dev fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
COPY valetudo_obstacle_image.py .
COPY entrypoint.sh .

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
