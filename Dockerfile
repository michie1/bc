FROM python:3

RUN apt-get update
RUN apt-get install cron coreutils -y
RUN apt-get install python-lxml -y

WORKDIR /src/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod 755 start.sh

RUN /usr/bin/crontab /src/crontab.txt

CMD ["./start.sh"]
