import boto3
import sys
import os

config_table = os.environ['config_table']
db = boto3.resource('dynamodb', region_name='us-east-1')
config = {}

def handler(event, context):
    global config
    count = 0
    try:
        config = db.Table(config_table).get_item(Key={ 
                "Key": "Config" 
            })['Item']['Value']

        out = db.Table(config['outboundQueueTable']).scan()
        count = out['Count']
    except Exception as e:
        print "ERROR(%s:%d): %s %s" % (sys._getframe().f_code.co_name, 
            sys._getframe().f_lineno, type(e).__name__, e.args[0])

    return count
