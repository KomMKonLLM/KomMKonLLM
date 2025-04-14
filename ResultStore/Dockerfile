FROM python:3.12

WORKDIR /ResultStore

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["./startup.sh"]
