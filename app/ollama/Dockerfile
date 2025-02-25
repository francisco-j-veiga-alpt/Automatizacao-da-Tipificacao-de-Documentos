FROM ollama/ollama:latest

COPY ./certificates /usr/local/share/ca-certificates/

RUN update-ca-certificates

EXPOSE 11434

# FROM ollama/ollama:latest

# COPY ./certificates /tmp/certificates  # Copy to a temporary location

# COPY entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh

# ENTRYPOINT ["/entrypoint.sh"]

# EXPOSE 11434