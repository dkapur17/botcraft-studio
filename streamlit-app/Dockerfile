FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    build-essential \
    curl \
    ffmpeg \
    nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY ./python-client /app/python-client
RUN pip install -e /app/python-client
COPY . /app
RUN mv /app/nltk_data /root/nltk_data
EXPOSE 80
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=80"]