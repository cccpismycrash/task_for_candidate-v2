FROM python:3.10.9

WORKDIR /app1

COPY requirements.txt /app1/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY database/ /app1/database/

COPY env/ /app1/env/

COPY config_reader.py /app1/config_reader.py

COPY main.py /app1/main.py

COPY processing.py /app1/processing.py

COPY small_logo.png /app1/small_logo.png

COPY stock-index-base-moex-rts-18122012-nowadays.xlsx /app1/stock-index-base-moex-rts-18122012-nowadays.xlsx

COPY Dockerfile /app1/Dockerfile

CMD [ "python", "main.py" ]