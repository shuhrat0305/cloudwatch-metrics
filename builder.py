import logging
import os
from config import Config
import yaml
import subprocess


class Builder:
    def __init__(self, configPath, otelConfigPath="./config_files/otel-config.yml",
                 cloudwatchConfigPath="./config_files/cloudwatch.yml") -> None:
        self.config = Config(configPath)
        self.logger = self.createLogger()
        self.otelConfigPath = otelConfigPath
        self.cloudwatchConfigPath = cloudwatchConfigPath

    # Initialize logger
    def createLogger(self) -> logging.Logger:
        DEFAULT_LOG_LEVEL = "INFO"
        LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        try:
            user_level = self.config.otel['logzio_log_level'].upper()
            level = user_level if user_level in LOG_LEVELS else DEFAULT_LOG_LEVEL
        except KeyError:
            level = DEFAULT_LOG_LEVEL

        logging.basicConfig(format='%(asctime)s\t\t%(levelname)s\t[%(name)s]\t%(filename)s:%(lineno)d\t%(message)s',
                            level=level)
        return logging.getLogger(__name__)

    # Takes dict representation of of yaml and dump it to a yaml file
    @staticmethod
    def dumpAndCloseFile(moduleYaml, moduleFile) -> None:
        yaml.preserve_quotes = True
        moduleFile.seek(0)
        yaml.dump(moduleYaml, moduleFile)
        moduleFile.truncate()
        moduleFile.close()

    # Takes user input and applies it to cloudwatch exporter
    def updateCloudwatchConfiguration(self, pathToNameSpaces='./cw_namespaces/') -> None:
        self.logger.info('Adding cloudwatch exporter configuration')
        with open(self.cloudwatchConfigPath, 'r+') as cloudwatchFile:
            values = yaml.safe_load(cloudwatchFile)
            # Add global settings
            values["period_seconds"] = self.config.cloudwatch['period_seconds']
            values["range_seconds"] = self.config.cloudwatch['range_seconds']
            values["delay_seconds"] = self.config.cloudwatch['delay_seconds']
            values["region"] = self.config.cloudwatch['region']
            if self.config.cloudwatch['role_arn'] != '':
                values["role_arn"] = self.config.cloudwatch['role_arn']
            # Add metrics
            for namespace in self.config.cloudwatch['aws_namespaces']:
                namespace = namespace.split('AWS/')[-1]
                with open('{}{}.yml'.format(pathToNameSpaces, namespace), 'r+') as namespaceFile:
                    namespaceYaml = yaml.safe_load(namespaceFile)
                    if namespaceYaml not in values['metrics']:
                        values['metrics'].extend(namespaceYaml)
                self.logger.info(f'AWS/{namespace} was added to cloudwatch exporter configuration')
            self.dumpAndCloseFile(values, cloudwatchFile)
        self.logger.info('Cloudwatch exporter configuration ready')
        self.logger.debug(f'Cloudwatch exporter configuration:\n{yaml.dump(values)}')

    # Takes user input and applies it to open telemetry collector
    def updateOtelConfiguration(self) -> None:
        self.logger.info('Adding opentelemtry collector configuration')
        with open(self.otelConfigPath, 'r+') as otelFile:
            values = yaml.safe_load(otelFile)
            # Update receiver
            values['receivers']['prometheus_exec']['scrape_interval'] = f"{self.config.otel['scrape_interval']}s"
            values['receivers']['prometheus_exec']['scrape_timeout'] = f"{self.config.otel['scrape_timeout']}s"
            values['receivers']['prometheus_exec']['env'] = []
            if self.config.otel['AWS_ACCESS_KEY_ID'] != "" and self.config.otel['AWS_SECRET_ACCESS_KEY'] != "":
                values['receivers']['prometheus_exec']['env'].append(
                    {
                        "name": "AWS_ACCESS_KEY_ID",
                        "value": self.config.otel['AWS_ACCESS_KEY_ID']
                    }
                )
                values['receivers']['prometheus_exec']['env'].append(
                    {
                        "name": "AWS_SECRET_ACCESS_KEY",
                        "value": self.config.otel['AWS_SECRET_ACCESS_KEY']
                    }
                )
            # Update exporter
            values['exporters']['prometheusremotewrite']['endpoint'] = self.config.getListenerUrl()
            values['exporters']['prometheusremotewrite']['timeout'] = f"{self.config.otel['remote_timeout']}s"
            values['exporters']['prometheusremotewrite']['headers'][
                'Authorization'] = f"Bearer {self.config.otel['token']}"
            values['exporters']['prometheusremotewrite']['external_labels']['p8s_logzio_name'] = self.config.otel[
                'p8s_logzio_name']
            # Update service
            values['service']['telemetry']['logs']['level'] = self.config.otel['log_level']
            self.dumpAndCloseFile(values, otelFile)
        self.logger.info('Opentelemtry collector configuration ready')
        self.logger.debug(f'Opentelemtry collector configuration:\n{yaml.dump(values)}')


if __name__ == '__main__':
    builder = Builder('./config_files/config.yml')
    builder.config.cloudwatch['aws_namespaces'], removed_namespaces = builder.config.validate()
    if removed_namespaces:
        builder.logger.warning(f'{removed_namespaces} namespaces are unsupported')
    if builder.config.cloudwatch["custom_config"] == "false":
        builder.updateCloudwatchConfiguration()
    else:
        builder.logger.info('Adding custom cloudwatch exporter configuration')
        with open(builder.cloudwatchConfigPath, 'r+') as cloudwatchFile:
            builder.logger.debug(f'Cloudwatch exporter configuration:\n{yaml.dump(yaml.safe_load(cloudwatchFile))}')
    builder.updateOtelConfiguration()
    os.system('chmod +x ./otelcontribcol_linux_amd64')
    subprocess.call(['./otelcontribcol_linux_amd64', '--config', './config_files/otel-config.yml'])
