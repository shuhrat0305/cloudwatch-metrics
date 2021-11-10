from os import environ
import yaml
import input_validator as iv


class Config:
    def __init__(self, configPath):
        # Try to load from config file
        with open(configPath) as f:
            dataMap = yaml.safe_load(f)
            self.__dict__.update(**dataMap)
        # Try to load from env variables
        # Open telemetry:
        if environ.get('SCRAPE_INTERVAL') is not None:
            self.otel['scrape_interval'] = int(environ.get('SCRAPE_INTERVAL'))
        if environ.get('LOGZIO_REGION') is not None:
            self.otel['logzio_region'] = environ.get('LOGZIO_REGION')
        if environ.get('TOKEN') is not None:
            self.otel['token'] = environ.get('TOKEN')
        if environ.get('P8S_LOGZIO_NAME') is not None:
            self.otel['p8s_logzio_name'] = environ.get('P8S_LOGZIO_NAME')
        if environ.get('CUSTOM_LISTENER') is not None:
            self.otel['custom_listener'] = environ.get('CUSTOM_LISTENER')
        if environ.get('REMOTE_TIMEOUT') is not None:
            self.otel['remote_timeout'] = int(environ.get('REMOTE_TIMEOUT'))
        if environ.get('SCRAPE_TIMEOUT') is not None:
            self.otel['scrape_timeout'] = int(environ.get('SCRAPE_TIMEOUT'))
        if environ.get('LOG_LEVEL') is not None:
            self.otel['log_level'] = environ.get('LOG_LEVEL')
        if environ.get('LOGZIO_LOG_LEVEL') is not None:
            self.otel['logzio_log_level'] = environ.get('LOGZIO_LOG_LEVEL')
        if environ.get('AWS_ACCESS_KEY_ID') is not None:
            self.otel['AWS_ACCESS_KEY_ID'] = environ.get('AWS_ACCESS_KEY_ID')
        if environ.get('AWS_SECRET_ACCESS_KEY') is not None:
            self.otel['AWS_SECRET_ACCESS_KEY'] = environ.get('AWS_SECRET_ACCESS_KEY')

        # Cloudwatch exporter:
        if environ.get('DELAY_SECONDS') is not None:
            self.cloudwatch['delay_seconds'] = int(environ.get('DELAY_SECONDS'))
        if environ.get('RANGE_SECONDS') is not None:
            self.cloudwatch['range_seconds'] = int(environ.get('RANGE_SECONDS'))
        if environ.get('PERIOD_SECONDS') is not None:
            self.cloudwatch['period_seconds'] = int(environ.get('PERIOD_SECONDS'))
        if environ.get('SET_TIMESTAMP') is not None:
            self.cloudwatch['set_timestamp'] = environ.get('SET_TIMESTAMP')
        if environ.get('AWS_REGION') is not None:
            self.cloudwatch['region'] = environ.get('AWS_REGION')
        if environ.get('AWS_NAMESPACES') is not None:
            self.cloudwatch['aws_namespaces'] = environ.get('AWS_NAMESPACES')
        if environ.get('CUSTOM_CONFIG') is not None:
            self.cloudwatch['custom_config'] = environ.get('CUSTOM_CONFIG')
        if environ.get('AWS_ROLE_ARN') is not None:
            self.cloudwatch['role_arn'] = environ.get('AWS_ROLE_ARN')

    # Validates user input
    def validate(self) -> (list, list):
        iv.is_valid_aws_region(self.cloudwatch['region'])
        iv.is_valid_logzio_token(self.otel['token'])
        iv.is_valid_p8s_logzio_name(self.otel['p8s_logzio_name'])
        iv.is_valid_logzio_region_code(self.otel['logzio_region'])
        iv.is_valid_interval(self.otel['scrape_interval'])
        iv.is_valid_interval(self.cloudwatch['delay_seconds'])
        iv.is_valid_interval(self.cloudwatch['range_seconds'])
        iv.is_valid_interval(self.cloudwatch['period_seconds'])
        iv.is_valid_interval(self.otel['scrape_timeout'])
        if self.cloudwatch['custom_config'] == 'true':
            return [], []
        else:
            return iv.is_valid_aws_namespaces(self.cloudwatch['aws_namespaces'])

    # Returns the listener url based on the region input
    def getListenerUrl(self) -> str:
        if self.otel['custom_listener'] != "":
            return self.otel['custom_listener']
        else:
            return "https://listener.logz.io:8053".replace("listener.", "listener{}.".format(self.getRegionCode(self.otel['logzio_region'])))

    @staticmethod
    def getRegionCode(region) -> str:
        if region != "us" and region != "":
            return "-{}".format(region)
        return ""
