FROM openjdk:11-slim
# Install Python
RUN apt-get update -y && apt-get install python3 -y && apt-get install python3-pip -y
COPY . .
RUN chmod +x otelcontribcol_linux_amd64
RUN pip install -r requirements.txt --user && \
    rm -f requirements.txt
EXPOSE 8888

CMD ["python3", "builder.py"]
