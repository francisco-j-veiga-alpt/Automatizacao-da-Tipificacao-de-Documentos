FROM python:3.12-slim

WORKDIR /app/src

COPY ./src /app/src
COPY requirements.txt /app/src

######
RUN pip config set global.proxy gateway.pt.zscaler.net:80
RUN pip config set global.trusted-host "pypi.python.org global.trusted-host pypi.org global.trusted-host files.pythonhosted.org"
######

RUN pip install -r requirements.txt

EXPOSE 80

CMD ["fastapi", "run", "/app/src/main.py", "--reload", "--port", "80"]