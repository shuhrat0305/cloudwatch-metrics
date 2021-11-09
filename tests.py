import os
import unittest
import yaml
from builder import Builder
from config import Config
import util.input_validator as iv
from util.data import aws_namespaces as ns_list


class TestBuilder(unittest.TestCase):
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
        os.environ['LOGZIO_REGION'] = 'eu'
        os.environ['SCRAPE_INTERVAL'] = '600'
        os.environ['P8S_LOGZIO_NAME'] = 'test'
        os.environ['PERIOD_SECONDS'] = '60'
        test_config = Config('./testdata/test-config.yml')
        os.environ.clear()
        self.assertEqual(test_config.otel['logzio_region'], 'eu')
        self.assertEqual(test_config.otel['scrape_interval'], 600)
        self.assertEqual(test_config.otel['p8s_logzio_name'], 'test')
        self.assertEqual(test_config.cloudwatch['period_seconds'], 60)

    def test_add_all_cloudwatch_namespaces(self):
        try:
            builder = Builder('./testdata/test-config.yml', cloudwatchConfigPath='./testdata/cloudwatch-test.yml')
            builder.config.cloudwatch['aws_namespaces'] = ns_list
            builder.updateCloudwatchConfiguration()
            with open(builder.cloudwatchConfigPath, 'r+') as cw:
                builder.dumpAndCloseFile({'metrics': []}, cw)
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
