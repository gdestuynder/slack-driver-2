#!/usr/bin/python

import boto3
import botocore
import driver
import json
import logging
import requests
import slack
import unittest
import utils

from unittest.mock import patch


logging.basicConfig(
   level=logging.DEBUG,
   format='%(asctime)s:%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class SlackDriverTest(unittest.TestCase):
    def setUp(self):
        pass

    @patch.object(requests, 'get')
    def test_get_access_rules(self, mock_request):
        class fake_request(object):
            fake_json = {'apps': { 'Slack': {'authorized_groups': ['team_moco']} }}
            text = json.dumps(fake_json)
            def ok(self):
                return True

        mock_request.return_value = fake_request
        driver.logger = logger
        ret = driver.get_access_rules('https://cdn.sso.mozilla.com/apps.yml')
        assert(ret['Slack']['authorized_groups'][0] == 'team_moco')

    @patch.object(driver, 'get_secret')
    @patch.object(slack.SlackAPI, 'get_users')
    @patch.object(slack.SlackAPI, 'deactivate_user')
    def test_verify_slack_users(self, mock_slack_deactivate, mock_slack_get_users, mock_get_secret):
        fake_users = [
                        {
                            'active': False,
                            'emails': [{'primary': True, 'value': 'inactive@example.net'}],
                            'id': 'U0000'
                        },
                        {
                            'active': True,
                            'emails': [{'primary': True, 'value': 'allowed@example.net'}],
                            'id': 'U0001'
                        }
                     ]

        fake_deactivate = { 'active': False }

        mock_get_secret.return_value = 'nope'
        mock_slack_get_users.return_value = fake_users
        mock_slack_deactivate = fake_deactivate

        logger.info('Check if allowed user stays allowed')
        ret = driver.verify_slack_users({'allowed@example.net': 'test'})
        assert(ret is True)

        logger.info('Check if inactive user is skipped')
        ret = driver.verify_slack_users({'inactive@example.net': 'test', 'allowed@example.net': 'test'})
        assert(ret is True)

        logger.info('Check if user without allowed group user is removed')
        ret = driver.verify_slack_users({})
        assert(ret is False)