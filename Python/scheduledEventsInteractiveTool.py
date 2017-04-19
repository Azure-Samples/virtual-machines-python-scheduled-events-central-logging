#!/usr/bin/python

import json
import socket
import sys
import getopt
import logging
from enum import Enum
from datetime import datetime
import base64
import hmac
import hashlib
import time
import urllib.request
import urllib.parse
import configparser

metadata_url = 'http://169.254.169.254/metadata/scheduledevents?api-version=2017-03-01'
headers = {'Metadata': 'true'}
this_host = socket.gethostname()
log_format = '%(asctime)s [%(levelname)s] %(message)s'
logger = logging.getLogger('example')
logging.basicConfig(format=log_format, level=logging.DEBUG)
config_key_endpoint = 'Endpoint'
config_key_shared_access_key_name = 'SharedAccessKeyName'
config_key_shared_access_key = 'SharedAccessKey'
config_key_entity_path = 'EntityPath'
encoding = 'utf-8'


class EventHubMsgSender:
    API_VERSION = '2016-07'
    TOKEN_VALID_SECS = 10
    TOKEN_FORMAT = 'SharedAccessSignature sig=%s&se=%s&skn=%s&sr=%s'

    def __init__(self, connectionString=None):
        if connectionString is None:
            config = configparser.ConfigParser()
            config.read('scheduledEventsInteractiveToolConfig.ini')
            connectionString = config['DEFAULT']['connectionstring']

        if connectionString is not None:
            keyValues = dict((item.split('=', 1))
                             for item in connectionString.split(';'))
            self.endPoint = keyValues[config_key_endpoint].replace('sb://', '')
            self.keyName = keyValues[config_key_shared_access_key_name]
            self.keyValue = keyValues[config_key_shared_access_key]
            self.entityPath = keyValues[config_key_entity_path]

    def _buildEventHubSasToken(self):
        expiry = int(time.time() + 10000)
        string_to_sign = '{}\n{}'.format(
            urllib.parse.quote_plus(self.endPoint), expiry)
        key = self.keyValue.encode(encoding)
        string_to_sign = string_to_sign.encode(encoding)
        signed_hmac_sha256 = hmac.HMAC(key, string_to_sign, hashlib.sha256)
        signature = signed_hmac_sha256.digest()
        signature = base64.b64encode(signature)
        token = 'SharedAccessSignature sr={}&sig={}&se={}&skn={}'.format(urllib.parse.quote_plus(
            self.endPoint), urllib.parse.quote(signature), expiry, self.keyName)
        return token

    def sendD2CMsg(self, message):
        sasToken = self._buildEventHubSasToken()
        url = 'https://{}{}/messages?api-version={}'.format(
            self.endPoint, self.entityPath, self.API_VERSION)
        data = message.encode('ascii')
        req = urllib.request.Request(
            url, headers={'Authorization': sasToken}, data=data, method='POST')
        with urllib.request.urlopen(req) as f:
            pass
        return f.read().decode(encoding)


def send_to_event_hub(eventHubMessage):
    ehMsgSender = EventHubMsgSender()
    messageAsJson = json.dumps(eventHubMessage, ensure_ascii=False)
    result = ehMsgSender.sendD2CMsg(messageAsJson)
    logger.debug('send_to_event_hub returned {}'.format(result))


def get_scheduled_events():
    logger.debug('get_scheduled_events was called')
    req = urllib.request.Request(url=metadata_url, headers=headers)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode(encoding))
    return data


def ack_event(evt):
    eventId = evt['EventId']
    logger.info('ack_event was called with eventID {}'.format(eventId))
    ack_msg = '{{"StartRequests":[{{"EventId":"{}"}}]}}'.format(eventId)
    ack_msg = ack_msg.encode()
    res = urllib.request.urlopen(url=metadata_url, data=ack_msg).read()
    eventHubMessage = build_eventhub_message(
        evt, 'Scheduled Event was acknowledged')
    send_to_event_hub(eventHubMessage)


def build_eventhub_message(evt, message):
    eventHubMessage = evt.copy()
    eventHubMessage['Hostname'] = this_host
    eventHubMessage['Time'] = datetime.now().strftime('%H:%M:%S')
    eventHubMessage['Msg'] = message
    if 'Resources' in evt:
        eventHubMessage['Resources'] = evt['Resources'][0]
    if 'NotBefore' in evt:
        eventHubMessage['NotBefore'] = evt['NotBefore'].replace(' ', '_')
    eventHubMessage['LogType'] = 'DEBUG'
    return eventHubMessage


def handle_scheduled_events(data):
    numEvents = len(data['Events'])
    logger.info(
        'handle_scheduled_events was called with {} events'.format(numEvents))
    if numEvents == 0:
        emptyEvent = {}
        eventHubMessage = build_eventhub_message(
            emptyEvent, 'No Scheduled Events')
        send_to_event_hub(eventHubMessage)
        return

    for evt in data['Events']:
        eventHubMessage = build_eventhub_message(
            evt, 'Scheduled Event was detected')
        logger.info(eventHubMessage)
        send_to_event_hub(eventHubMessage)
        if this_host in eventHubMessage['Resources']:
            eventId = evt['EventId']
            logger.info('THIS host ({}) is scheduled for {} not before {} (id: {})'.format(
                this_host, eventHubMessage['EventType'], eventHubMessage['NotBefore'], eventId))
            userAck = input('Are you looking to acknowledge the event (y/n)?')
            if userAck == 'y':
                logger.debug('Acknowledging {}'.format(eventId))
                ack_event(evt)
            else:
                logger.debug('Ignoring {}'.format(eventId))


def main():
    logger.debug('Azure Scheduled Events Interactive Tool')
    data = get_scheduled_events()
    handle_scheduled_events(data)

if __name__ == '__main__':
    main()
    sys.exit(0)
