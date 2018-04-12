import sys
import os
sys.path.insert(0, "./lib")
from pypodio2 import api
import json
import boto3

config_table = os.environ['config_table']
db           = boto3.resource('dynamodb', region_name='us-east-1')

def extract_contact(u):
    out = []
    for v in u['values']:
        user = {
            'id': '',
            'name': '',
            'phones': [],
            'mail': []
        }
        if 'value' in v:
            if 'user_id' in v['value']:
                user['id'] = v['value']['user_id']
            if 'phone' in v['value']:
                user['phones'] += v['value']['phone']
            if 'mail' in v['value']:
                user['mail'] += v['value']['mail']
            if 'name' in v['value']:
                user['name'] = v['value']['name']
            out.append(user)
    return out

def lambda_handler(event, context):
    global config

    contacts = {
        'primary': [],
        'backup': [],
        'manager': [],
        'itms': []
    }

    try:
        config = db.Table(config_table).get_item(Key={ 
                "Key": "Config" 
            })['Item']['Value']

        client_id     = config['podioClientID']
        client_secret = config['podioClientSecret']
        s_app_id      = config['podioAppID']
        s_app_token   = config['podioAppToken']
    
        field_project        = int(config['podioProjectFieldID'])
        field_project_date   = int(config['podioStaffingDateFieldID'])
        field_project_type   = int(config['podioStaffingTypeFieldID'])
        
        oncall_project = int(config['podioITMSProjectID'])
        oncall_type    = int(config['podioTypeOnCall'])
    
    
        c = api.OAuthAppClient(
            client_id, 
            client_secret, 
            s_app_id, 
            s_app_token,
        )
        itms_staffing = c.Item.filter(s_app_id, attributes={
            'filters': {
                field_project     : [oncall_project],
                #field_project_type: [oncall_type],
                field_project_date: {"from": '+0dr', "to": '+0dr' }
            }
        })
    
    
        user_data = []
        for s in itms_staffing['items']:
            oncall = False
            primary_data = []
            second_data = []
            escalation_data = []
            for f in s['fields']:
                if f['field_id'] == field_project_type and f['values'][0]['value']['id'] == oncall_type:
                    oncall = True
                elif f['external_id'] == 'meeting-participants':
                    primary_data = extract_contact(f)
                elif f['external_id'] == 'second-resource':
                    second_data = extract_contact(f)
                elif f['external_id'] == 'escalation-point':
                    escalation_data = extract_contact(f)
            if oncall:
                contacts['primary'] = primary_data
                contacts['backup'] = second_data
                contacts['manager'] = escalation_data
            else:
                contacts['itms'] += primary_data
    except Exception as e:
        print "ERROR(lambda_handler): %s %s" % (type(e).__name__, e.args[0])

    return contacts

