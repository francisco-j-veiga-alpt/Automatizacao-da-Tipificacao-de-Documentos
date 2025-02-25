FROM python:3.12-slim

WORKDIR /app/backend/src

COPY ./src /app/backend/src
COPY requirements.txt /app/backend/src

######
RUN pip config set global.proxy gateway.pt.zscaler.net:80
RUN pip config set global.trusted-host "pypi.python.org global.trusted-host pypi.org global.trusted-host files.pythonhosted.org"
######

RUN pip install -r requirements.txt

EXPOSE 80

CMD ["fastapi", "run", "/app/backend/src/main.py", "--reload", "--host", "0.0.0.0", "--port", "80"]