FROM python:3.12-alpine

WORKDIR /data

COPY requirements.txt /data

RUN pip install --no-cache-dir -r requirements.txt

COPY . /data/

EXPOSE 5004

CMD ["python","app.py"]