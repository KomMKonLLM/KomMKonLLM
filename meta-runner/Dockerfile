FROM eclipse-temurin:8-jre
COPY --from=python:3.12 / /

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN python -m spacy download en_core_web_sm
COPY . .

CMD [ "python3", "src/main.py"] 	
