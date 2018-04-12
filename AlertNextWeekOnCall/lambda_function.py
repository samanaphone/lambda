import sys
import os
sys.path.insert(0, "./lib")
from pypodio2 import api
import boto3

def handler(event, context):
    client_id     = os.environ['client_id']
    client_secret = os.environ['client_secret']
    s_app_id      = int(os.environ['s_app_id']) # Staffing app
    s_app_token   = os.environ['s_app_token']   # Staffing token

    emails = get_emails()
    if len(emails) < 1: 
        print "ERROR: Cannot get SDMs emails for alert"
        return {}

    c = api.OAuthAppClient(
            client_id, 
            client_secret, 
            s_app_id, 
            s_app_token,
        )
    
    field_week_number    = 140525289
    field_project        = 140523653
    field_project_date   = 140522955
    field_project_type   = 140524037
    
    oncall_project = 772605447
    oncall_type    = 4
    
    a = {
        "filters": { 
            field_project     : [oncall_project],
            field_project_type: [oncall_type],
            field_project_date: {"from": '+4dr', "to": '+4dr' }
            },
    }

    t = c.Item.filter(s_app_id, a)
    
    if int(t['filtered']) < 1:
        res = send_email(emails)
    else:
        res = {}

    return res

def get_emails():
    client_id     = os.environ['client_id']
    client_secret = os.environ['client_secret']
    app_id        = int(os.environ['projects_app_id'])
    app_token     = os.environ['projects_token']
    oncall_project = int(os.environ['oncall_project_id'])


    c = api.OAuthAppClient(
            client_id, 
            client_secret, 
            app_id, 
            app_token,
        )
    a = { "filters": { "item_id": oncall_project } }
    t = c.Item.filter(app_id, a)
    if t['filtered'] != 1:
        print "ERROR: Cannot find the project for Managed Services"
        return []

    sdm_field_id = 140858054
    emails = []
    for f in t['items'][0]['fields']:
        if f['field_id'] == sdm_field_id:
            for i in f['values']:
                emails += i['value']['mail']
            break;
    return emails

def send_email(emails):
    client = boto3.client('ses')
    
    message = """
Hello, this is a message from Samana\'s Phone System.

You are receiving this message, because next week there is no assignment
for OnCall. This means that in a few days the system will not be able
to accept calls, because no agents will be available.

Please access Podio and assign a resource to OnCall for next week.

If you don't do this whithin the next 24 hours, you'll get this meesage 
again.

Thank you

Samana's Phone System

"""
    
    response = client.send_email(
        Source='phonesystem@samanagroup.com',
        Destination={
            'ToAddresses': emails
        },
        Message={
            'Subject': {
                'Data': 'ALERT!! OnCall assignment for next week not configured',
                'Charset': 'utf8'
            },
            'Body': {
                'Text': {
                    'Data': message,
                    'Charset': 'utf8'
                }
            }
        }
    )
    return response
