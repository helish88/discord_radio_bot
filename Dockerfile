FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip

RUN apt-get update && apt-get install -y git

RUN pip install -r /app/requirements.txt

COPY . /app

CMD ["python", "/app/main.py"]
