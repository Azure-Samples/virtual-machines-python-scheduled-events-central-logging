#!/usr/bin/python

import json
import socket
import sys, getopt
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

metadata_url="http://169.254.169.254/metadata/latest/scheduledevents"
headers="{Metadata:true}"
this_host=socket.gethostname()
log_format = " %(asctime)s [%(levelname)s] %(message)s"
logger = logging.getLogger('example')
logging.basicConfig(format=log_format, level=logging.DEBUG)


class EventHubMsgSender:
    
    API_VERSION = '2016-07'
    TOKEN_VALID_SECS = 10
    TOKEN_FORMAT = 'SharedAccessSignature sig=%s&se=%s&skn=%s&sr=%s'
    
    def __init__(self, connectionString=None):
        if connectionString == None:
            config = configparser.ConfigParser()
            config.read('scheduledEventsInteractiveToolConfig.ini')
            connectionString = config['DEFAULT']['connectionstring']
            connectionString = connectionString.replace("sb://","")

        if connectionString != None:
            endPoint, keyName, keyValue, entityPath = [sub[sub.index('=') + 1:] for sub in connectionString.split(";")]
            self.endPoint = endPoint
            self.keyName = keyName
            self.keyValue = keyValue
            self.entityPath = entityPath
   
    def _buildEventHubSasToken (self):
        expiry = int(time.time() + 10000)
        string_to_sign = urllib.parse.quote_plus(self.endPoint) + '\n' + str(expiry)        
        key = self.keyValue.encode('utf-8')
        string_to_sign = string_to_sign.encode('utf-8')
        signed_hmac_sha256 = hmac.HMAC(key, string_to_sign, hashlib.sha256)
        signature = signed_hmac_sha256.digest()
        signature = base64.b64encode(signature)
        return 'SharedAccessSignature sr=' + urllib.parse.quote_plus(self.endPoint)  + '&sig=' + urllib.parse.quote(signature) + '&se=' + str(expiry) + '&skn=' + self.keyName

    def sendD2CMsg(self, message):
        sasToken = self._buildEventHubSasToken()
        url = 'https://%s%s/messages?api-version=%s' % (self.endPoint,  self.entityPath,self.API_VERSION)
        data = message.encode ('ascii')
        req = urllib.request.Request (url, headers={'Authorization': sasToken}, data=data, method='POST')
        with urllib.request.urlopen(req) as f:
            pass
        return f.read().decode('utf-8')


def send_to_event_hub (evt):
    ehMsgSender = EventHubMsgSender()
    result=  ehMsgSender.sendD2CMsg(evt)
    logger.debug ("send_to_event_hub returned "+ result)


def get_scheduled_events():
   logger.debug ("get_scheduled_events was called")
   req=urllib.request.Request(metadata_url)
   req.add_header('Metadata','true')
   resp=urllib.request.urlopen(req)
   data=json.loads(resp.read().decode('utf8'))
   '''logger.debug ("scheduled events: \n:"+data)'''
   return data

def ack_event(evt):
    logger.info ("ack_event was called with eventID "+ evt['EventId'])
    ack_msg="{\"StartRequests\":[{\"EventId\":\""+evt['EventId'] +"\"}]}"
    ack_msg=ack_msg.encode()
    res=urllib.request.urlopen("http://169.254.169.254/metadata/latest/scheduledevents", data=ack_msg).read()
    current_time = datetime.now().strftime('%H:%M:%S')
    ehMsg = '{ "Hostname":"' + this_host+ '","Time":"'+current_time+'","LogType":"INFO","Msg":"Scheduled Event was acknowledged","EventID":"'+evt['EventId']+'"}'
    send_to_event_hub(ehMsg)

def handle_scheduled_events(data):
    logger.info ("handle_scheduled_events was called with "+ str(len(data['Events'])))
    if len(data['Events']) == 0:
        current_time = datetime.now().strftime('%H:%M:%S')
        ehMsg = '{ "Hostname":"' + this_host+ '","Time":"'+current_time+'","LogType":"DEBUG","Msg":"No Scheduled Events"}'
        send_to_event_hub(ehMsg)     

    for evt in data['Events']:
        eventid=evt['EventId']
        status=evt['EventStatus']
        resources=evt['Resources'][0]
        eventype=evt['EventType']
        restype=evt['ResourceType']
        notbefore=evt['NotBefore'].replace(" ","_")
        logger.info ("EventId: "+ eventid+ " Type: "+ eventype+" Status: "+ status+" Resource: "+resources)

        current_time = datetime.now().strftime('%H:%M:%S')
        ehMsg = '{ "Hostname":"' + this_host+ '","Time":"'+current_time+'","LogType":"INFO","Msg":"Scheduled Event was detected","EventID":"'+eventid+'","EventType":"'+eventype+'","Resource":"'+resources+'","NotBefore":"'+notbefore+'"}'
        send_to_event_hub(ehMsg)

        if this_host in evt['Resources'][0]:
            logger.info ("THIS host is scheduled for " + eventype + " not before " + notbefore)
            userAck = input ('Are you looking to acknowledge the event (y/n)? ')
            if userAck == 'y':
                ack_event (evt)
            

def log_event (eventType,message):
    print (eventType.name + " : " +  message)

def main():
    logger.debug ("Azure Scheduled Events Interactive Tool")
    data=get_scheduled_events()
    handle_scheduled_events(data)


if __name__ == '__main__':
  main()
  sys.exit(0)
