FROM python:3.12-slim


RUN apt-get update && \
    apt-get install -y curl wget && \
    # Clean up apt cache to reduce image size
    rm -rf /var/lib/apt/lists/*

# Copia o certificado da proxy
COPY ./cert/prxcfw.telecom.pt.crt /usr/local/share/ca-certificates/
 
# Atualiza os certificados do sistema
RUN update-ca-certificates
 
# Encontra o caminho do certifi


WORKDIR /app/backend/src

COPY ./src /app/backend/src
COPY requirements.txt /app/backend/src

######
RUN pip config set global.proxy gateway.pt.zscaler.net:80
RUN pip config set global.trusted-host "pypi.python.org global.trusted-host pypi.org global.trusted-host files.pythonhosted.org"
######

RUN pip install -r requirements.txt

ENV http_proxy=http://10.18.117.210:8080
ENV https_proxy=http://10.18.117.210:8080
ENV no_proxy=10.*,*.local,*.corppt.com,*.telecom.pt

RUN CERTIFI_PATH=$(python -m certifi) && \
    echo "Appending proxy cert to certifi bundle at $CERTIFI_PATH" && \
    cat /usr/local/share/ca-certificates/prxcfw.telecom.pt.crt >> $CERTIFI_PATH

EXPOSE 80

CMD ["fastapi", "run", "/app/backend/src/main.py", "--reload", "--host", "0.0.0.0", "--port", "80"]