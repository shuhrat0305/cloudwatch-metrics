import os
import unittest

import yaml

from builder import Builder
from config import Config
import input_validator as iv
from testdata.data import aws_namespaces as ns_list


class TestBuilder(unittest.TestCase):
    def test_getRegionCode(self):
        test_config = Config('./testdata/test-config.yml')
        valid_ns = ["au", "ca", "eu", "nl", "uk", "wa"]
        for ns in valid_ns:
            self.assertEqual(test_config.getRegionCode(ns), f"-{ns}")

    def test_get_listener_url(self):
        test_config = Config('./testdata/test-config.yml')
        self.assertEqual(test_config.getListenerUrl(), 'https://listener.logz.io:8053')
        valid_ns = ["au", "ca", "eu", "nl", "uk", "wa"]
        for ns in valid_ns:
            test_config.otel['logzio_region'] = ns
            self.assertEqual(test_config.getListenerUrl(), f'https://listener-{ns}.logz.io:8053')

        test_config.otel['custom_listener'] = 'test'
        self.assertEqual(test_config.getListenerUrl(), test_config.otel['custom_listener'])

    def test_load_config(self):
        # otel
        test_config = Config('./testdata/test-config.yml')
        self.assertEqual(test_config.otel['logzio_region'], 'us')
        self.assertEqual(test_config.otel['custom_listener'], '')
        self.assertEqual(test_config.otel['p8s_logzio_name'], 'cloudwatch-metrics')
        self.assertEqual(test_config.otel['token'], 'fakeXamgZErKKkMhmzdVZDhuZcpGKXeo')
        self.assertEqual(test_config.otel['scrape_interval'], 300)
        self.assertEqual(test_config.otel['remote_timeout'], 120)
        self.assertEqual(test_config.otel['log_level'], 'debug')
        self.assertEqual(test_config.otel['logzio_log_level'], 'info')
        self.assertEqual(test_config.otel['AWS_ACCESS_KEY_ID'], 'fakeXamgZErKKkMhmzdVZDhuZcpGKXeo')
        self.assertEqual(test_config.otel['AWS_SECRET_ACCESS_KEY'], 'fakeXamgZErKKkMhmzdVZDhuZcpGKXeo')
        # cloudwatch
        self.assertEqual(test_config.cloudwatch['custom_config'], 'false')
        self.assertEqual(test_config.cloudwatch['region'], 'us-east-1')
        self.assertEqual(test_config.cloudwatch['role_arn'], '')
        self.assertEqual(test_config.cloudwatch['aws_namespaces'], ["AWS/Lambda", "AWS/EC2"])
        self.assertEqual(test_config.cloudwatch['set_timestamp'], 'false')
        self.assertEqual(test_config.cloudwatch['delay_seconds'], 600)
        self.assertEqual(test_config.cloudwatch['range_seconds'], 600)
        self.assertEqual(test_config.cloudwatch['period_seconds'], 300)
        # Success
        try:
            Config('./testdata/test-config.yml')
        except Exception as e:
            self.fail(f'Unexpected error {e}')

    def test_load_config_env_overwrite(self):
        # otel
        os.environ['LOGZIO_REGION'] = 'eu'
        os.environ['SCRAPE_INTERVAL'] = '600'
        os.environ['P8S_LOGZIO_NAME'] = 'test'
        os.environ['TOKEN'] = 'test'
        os.environ['CUSTOM_LISTENER'] = 'test'
        os.environ['REMOTE_TIMEOUT'] = '600'
        os.environ['LOG_LEVEL'] = 'info'
        os.environ['LOGZIO_LOG_LEVEL'] = 'debug'
        os.environ['AWS_ACCESS_KEY_ID'] = 'test'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
        # cloudwatch
        os.environ['DELAY_SECONDS'] = '60'
        os.environ['RANGE_SECONDS'] = '60'
        os.environ['PERIOD_SECONDS'] = '60'
        os.environ['SET_TIMESTAMP'] = 'true'
        os.environ['AWS_REGION'] = 'us-east-2'
        os.environ['AWS_NAMESPACES'] = 'AWS/RDS,AWS/ELB'
        os.environ['CUSTOM_CONFIG'] = 'true'
        os.environ['AWS_ROLE_ARN'] = 'test'
        test_config = Config('./testdata/test-config.yml')
        os.environ.clear()
        # otel
        self.assertEqual(test_config.otel['logzio_region'], 'eu')
        self.assertEqual(test_config.otel['scrape_interval'], 600)
        self.assertEqual(test_config.otel['token'], 'test')
        self.assertEqual(test_config.otel['custom_listener'], 'test')
        self.assertEqual(test_config.otel['remote_timeout'], 600)
        self.assertEqual(test_config.otel['log_level'], 'info')
        self.assertEqual(test_config.otel['logzio_log_level'], 'debug')
        self.assertEqual(test_config.otel['AWS_ACCESS_KEY_ID'], 'test')
        self.assertEqual(test_config.otel['AWS_SECRET_ACCESS_KEY'], 'test')
        # cloudwatch
        self.assertEqual(test_config.cloudwatch['custom_config'], 'true')
        self.assertEqual(test_config.cloudwatch['region'], 'us-east-2')
        self.assertEqual(test_config.cloudwatch['role_arn'], 'test')
        self.assertEqual(test_config.cloudwatch['aws_namespaces'], 'AWS/RDS,AWS/ELB')
        self.assertEqual(test_config.cloudwatch['delay_seconds'], 60)
        self.assertEqual(test_config.cloudwatch['range_seconds'], 60)
        self.assertEqual(test_config.cloudwatch['period_seconds'], 60)
        self.assertEqual(test_config.cloudwatch['set_timestamp'], 'true')

    def test_add_all_cloudwatch_namespaces(self):
        try:
            builder = Builder('./testdata/test-config.yml', cloudwatchConfigPath='./testdata/cloudwatch-test.yml')
            builder.config.cloudwatch['aws_namespaces'] = ns_list
            builder.updateCloudwatchConfiguration('./cw_namespaces/')
            with open(builder.cloudwatchConfigPath, 'r+') as cw:
                builder.dumpAndCloseFile({'metrics': []}, cw)
        except Exception as e:
            self.fail(f'Unexpected error {e}')

    def test_cloudwatch_config(self):
        try:
            builder = Builder('./testdata/test-config.yml', cloudwatchConfigPath='./testdata/cloudwatch-test.yml')
            builder.config.cloudwatch['aws_namespaces'], remove = iv.is_valid_aws_namespaces('AWS/EC2,AWS/RDS')
            builder.updateCloudwatchConfiguration('./cw_namespaces/')
            with open(builder.cloudwatchConfigPath, 'r+') as cw:
                builder.dumpAndCloseFile({'metrics': []}, cw)
        except Exception as e:
            self.fail(f'Unexpected error {e}')

    def test_update_otel_collector(self):
        try:
            builder = Builder('./testdata/test-config.yml', otelConfigPath='./testdata/otel-test.yml')
            with open(builder.otelConfigPath, 'r+') as otel:
                builder.updateOtelConfiguration()
                values = yaml.safe_load(otel)
                self.assertEqual(values['receivers']['prometheus_exec']['scrape_interval'], '300s')
                self.assertEqual(values['receivers']['prometheus_exec']['scrape_timeout'], '300s')
                self.assertEqual(values['exporters']['prometheusremotewrite']['endpoint'],
                                 'https://listener.logz.io:8053')
                self.assertEqual(values['exporters']['prometheusremotewrite']['timeout'], '120s')
                self.assertEqual(values['exporters']['prometheusremotewrite']['external_labels']['p8s_logzio_name'],
                                 'cloudwatch-metrics')
                self.assertEqual(values['exporters']['prometheusremotewrite']['headers']['Authorization'],
                                 'Bearer fakeXamgZErKKkMhmzdVZDhuZcpGKXeo')
                self.assertEqual(values['service']['telemetry']['logs']['level'], 'debug')
                # reset config
                with open('./testdata/default-otel.yml', 'r+') as otel_def:
                    testing_otel_yaml = yaml.safe_load(otel_def)
                    builder.dumpAndCloseFile(testing_otel_yaml, otel)
        except Exception as e:
            self.fail(f'Unexpected error {e}')


class TestInput(unittest.TestCase):
    def test_is_valid_logzio_token(self):
        # Fail Type
        non_valid_types = [-2, None, 4j, ['string', 'string']]
        for t in non_valid_types:
            self.assertRaises(TypeError, iv.is_valid_logzio_token, t)
        # Fail Value
        non_valid_vals = ['12', 'quwyekclshyrflclhf', 'rDRJEidvpIbecUwshyCn4kuUjbymiHev']
        for v in non_valid_vals:
            self.assertRaises(ValueError, iv.is_valid_logzio_token, v)
        # Success
        try:
            iv.is_valid_logzio_token('rDRJEidvpIbecUwshyCnGkuUjbymiHev')
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')

    def test_is_valid_logzio_region_code(self):
        # Fail Type
        non_valid_types = [-2, None, 4j, ['string', 'string']]
        for t in non_valid_types:
            self.assertRaises(TypeError, iv.is_valid_logzio_region_code, t)
        # Fail Value
        non_valid_vals = ['12', 'usa', 'au,ca']
        for v in non_valid_vals:
            self.assertRaises(ValueError, iv.is_valid_logzio_region_code, v)
        # Success
        try:
            iv.is_valid_logzio_region_code('ca')
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')
        try:
            iv.is_valid_logzio_region_code('us')
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')

    def test_is_valid_scrape_interval(self):
        # Fail type
        non_valid_types = ['12', None, False, ['string', 'string'], 4j]
        for t in non_valid_types:
            self.assertRaises(TypeError, iv.is_valid_interval, t)
        # Fail Value
        non_valid_vals = [-60, 55, 10, 306]
        for v in non_valid_vals:
            self.assertRaises(ValueError, iv.is_valid_interval, v)
        # Success
        try:
            iv.is_valid_interval(360000)
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')
        try:
            iv.is_valid_interval(60)
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')

    def test_is_valid_aws_namespaces(self):
        # Fail Value
        self.assertRaises(ValueError, iv.is_valid_aws_namespaces, '')
        self.assertRaises(ValueError, iv.is_valid_aws_namespaces, 'AWS/ec2,  aws/RDS, AWS/lambda, AWS/fdfdf')
        # Success
        self.assertTupleEqual(iv.is_valid_aws_namespaces('AWS/RDS,AWS/Lambda,AWS/CloudFront'),
                              (['AWS/CloudFront', 'AWS/Lambda', 'AWS/RDS'], []))
        self.assertTupleEqual(iv.is_valid_aws_namespaces('AWS/RDS,AWS/nosuch,AWS/Lambda,AWS/CloudFront'),
                              (['AWS/CloudFront', 'AWS/Lambda', 'AWS/RDS'], ['AWS/nosuch']))
        self.assertTupleEqual(iv.is_valid_aws_namespaces('AWS/RDS,AWS/Lambda,AWS/Cloudfront'),
                              (['AWS/Lambda', 'AWS/RDS'], ['AWS/Cloudfront']))
        self.assertTupleEqual(iv.is_valid_aws_namespaces('AWS/RDS, AWS/RDS,  AWS/Lambda,AWS/Lambda,AWS/Cloudfront'),
                              (['AWS/Lambda', 'AWS/RDS'], ['AWS/Cloudfront']))

    def test_is_valid_p8s_logzio_name(self):
        # Fail Type
        non_valid_types = [-2, None, 4j, ['string', 'string']]
        for t in non_valid_types:
            self.assertRaises(TypeError, iv.is_valid_p8s_logzio_name, t)
        # Success
        try:
            iv.is_valid_p8s_logzio_name('dev5')
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')

    def test_is_valid_custom_listener(self):
        # Fail Type
        non_valid_types = [-2, None, 4j, ['string', 'string']]
        for t in non_valid_types:
            self.assertRaises(TypeError, iv.is_valid_custom_listener, t)
        # Fail Value
        non_valid_vals = ['12', 'www.custom.listener:3000', 'custom.listener:3000', 'htt://custom.listener:3000',
                          'https://custom.listener:', 'https://custom.']
        for v in non_valid_vals:
            self.assertRaises(ValueError, iv.is_valid_custom_listener, v)
        # Success
        try:
            iv.is_valid_custom_listener('http://custom.listener:3000')
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')
        try:
            iv.is_valid_custom_listener('https://localhost:9200')
        except (TypeError, ValueError) as e:
            self.fail(f'Unexpected error {e}')


if __name__ == '__main__':
    unittest.main()
