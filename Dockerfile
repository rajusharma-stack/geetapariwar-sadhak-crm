FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data

ENV GEETAPARIWAR_DATA_DIR=/data
ENV SECRET_KEY=change-this-to-a-random-secret-key

EXPOSE 3201

CMD ["gunicorn", "--bind", "0.0.0.0:3201", "--workers", "2", "--timeout", "120", "wsgi:application"]
