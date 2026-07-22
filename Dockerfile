FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data && chmod +x start.sh
COPY data/crm.db /data/crm.db

ENV GEETAPARIWAR_DATA_DIR=/data
ENV SECRET_KEY=change-this-to-a-random-secret-key

EXPOSE 3201

CMD ["./start.sh"]
