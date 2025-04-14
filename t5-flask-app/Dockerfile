FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --timeout=600 -r requirements.txt --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --trusted-host files.pythonhosted.org

COPY . .

CMD [ "python3", "src/main.py", "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python"] 	
