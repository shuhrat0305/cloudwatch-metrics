FROM openjdk:11-slim
# Install Python
RUN apt-get update -y && apt-get install python3 -y && apt-get install python3-pip -y && apt-get install curl -y

# Copy files
COPY config_files config_files
COPY cw_namespaces cw_namespaces
COPY testdata testdata
COPY builder.py builder.py
COPY config.py config.py
COPY input_validator.py input_validator.py
COPY cloudwatch_exporter-0.11.0-jar-with-dependencies.jar cloudwatch_exporter-0.11.0-jar-with-dependencies.jar
COPY requirements.txt requirements.txt

# Download opentelemetry binary
RUN curl -O https://integration-binaries.s3.amazonaws.com/otelcontribcol_linux_amd64
RUN chmod +x otelcontribcol_linux_amd64
# Install dependencies
RUN pip install -r requirements.txt --user && \
    rm -f requirements.txt
# Opentelemetry metrics
EXPOSE 8888
# Zpages
EXPOSE 55679
# Health check
EXPOSE 13133
# Pprof
EXPOSE 1777

CMD ["python3", "builder.py"]
