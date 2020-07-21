import sys
import os
sys.path.insert(0, "./lib")
from pypodio2 import api
import json
import boto3
from datetime import tzinfo, timedelta, datetime

config_table = os.environ['config_table']
db           = boto3.resource('dynamodb', region_name='us-east-1')

"""
Code extracted from Python documentation 
https://docs.python.org/2/library/datetime.html

Start
"""
ZERO = timedelta(0)
HOUR = timedelta(hours=1)

def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += timedelta(days_to_go)
    return dt

DSTSTART_2007 = datetime(1, 3, 8, 2)
DSTEND_2007 = datetime(1, 11, 1, 1)
DSTSTART_1987_2006 = datetime(1, 4, 1, 2)
DSTEND_1987_2006 = datetime(1, 10, 25, 1)
DSTSTART_1967_1986 = datetime(1, 4, 24, 2)
DSTEND_1967_1986 = DSTEND_1987_2006

class USTimeZone(tzinfo):
    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname
    def __repr__(self):
        return self.reprname
    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname
    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)
    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            # An exception may be sensible here, in one or both cases.
            # It depends on how you want to treat them.  The default
            # fromutc() implementation (called by the default astimezone()
            # implementation) passes a datetime with dt.tzinfo is self.
            return ZERO
        assert dt.tzinfo is self
        # Find start and end times for US DST. For years before 1967, return
        # ZERO for no DST.
        if 2006 < dt.year:
            dststart, dstend = DSTSTART_2007, DSTEND_2007
        elif 1986 < dt.year < 2007:
            dststart, dstend = DSTSTART_1987_2006, DSTEND_1987_2006
        elif 1966 < dt.year < 1987:
            dststart, dstend = DSTSTART_1967_1986, DSTEND_1967_1986
        else:
            return ZERO
        start = first_sunday_on_or_after(dststart.replace(year=dt.year))
        end = first_sunday_on_or_after(dstend.replace(year=dt.year))
        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        if start <= dt.replace(tzinfo=None) < end:
            return HOUR
        else:
            return ZERO

Eastern  = USTimeZone(-5, "Eastern",  "EST", "EDT")

"""
Code extracted from Python documentation 
https://docs.python.org/2/library/datetime.html
Out:
 Contact_info: {
    'id': 'xxxx',
    'name': 'xxxx',
    'phones': [ '11111', '2222' ],
    'mail': [ 'asdf@xxxx', 'qwer@eeeee' ]
 }
End
"""
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

def notnone(val1, val2, default):
    if val1 is not None:
        return val1
    elif val2 is not None:
        return val2
    else:
        return default

def lambda_handler(event, context):
'''
Out:
    {
        'primary': { !!Contact_info!! },
        'backup': { !!Contact_info!! },
        'manager': { !! Contact_info!! }
    }
'''
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

        client_id       = config['podioClientID']
        client_secret   = config['podioClientSecret']
        s_app_id        = config['podioAppID']
        s_app_token     = config['podioAppToken']
        itms_call_start = datetime.strptime(config['itms_call_start'], "%H:%M").time()
        itms_call_end   = datetime.strptime(config['itms_call_end'], "%H:%M").time()
        now             = datetime.now(Eastern).time()
        always_4_oncall = config['always4oncall']
    
        field_project        = int(config['podioProjectFieldID'])
        field_project_date   = int(config['podioStaffingDateFieldID'])
        field_project_type   = int(config['podioStaffingTypeFieldID'])
        
        oncall_project = int(config['podioITMSProjectID'])
        oncall_type    = int(config['podioTypeOnCall'])
        default_contact = config['defaultContact']
    
    
        c = api.OAuthAppClient(
            client_id, 
            client_secret, 
            s_app_id, 
            s_app_token,
        )
        itms_staffing = c.Item.filter(s_app_id, attributes={
            'filters': {
                field_project     : [oncall_project],
                field_project_date: {"from": '+0dr', "to": '+0dr' }
            }
        })
        call_4_oncall = always_4_oncall or (now < itms_call_start  or now > itms_call_end)

        itms_primary_data = None
        itms_second_data = None
        itms_escalation_data = None
        oncall_primary_data = None
        oncall_second_data = None
        oncall_escalation_data = None
        for s in itms_staffing['items']:
            define_callee = False
            primary_data = []
            second_data = []
            escalation_data = []
            expired_staffing = False
            project_type = 0
            for f in s['fields']:
                if f['field_id'] == field_project_type:
                    project_type = int(f['values'][0]['value']['id'])
                elif f['external_id'] == 'meeting-participants':
                    primary_data = extract_contact(f)
                elif f['external_id'] == 'second-resource':
                    second_data = extract_contact(f)
                elif f['external_id'] == 'escalation-point':
                    escalation_data = extract_contact(f)
                elif f['field_id'] == field_project_date:
                    d = datetime.strptime(f['values'][0]['end_utc'], '%Y-%m-%d %H:%M:%S')
                    expired_staffing = d < datetime.now()

            if expired_staffing:
                continue

            if project_type == oncall_type:
                oncall_primary_data = primary_data
                oncall_second_data = second_data
                oncall_escalation_data = escalation_data
            else:
                itms_primary_data = primary_data
                itms_second_data = second_data
                itms_escalation_data = escalation_data

        #oncall_primary_data = None
        #itms_primary_data = None
        if call_4_oncall:
            contacts['primary'] = notnone(oncall_primary_data,    itms_primary_data,    [default_contact])
            contacts['backup']  = notnone(oncall_second_data,     itms_second_data,     [default_contact])
            contacts['manager'] = notnone(oncall_escalation_data, itms_escalation_data, [default_contact])
        else:
            contacts['primary'] = notnone(itms_primary_data,    oncall_primary_data,    [default_contact])
            contacts['backup']  = notnone(itms_second_data,     oncall_second_data,     [default_contact])
            contacts['manager'] = notnone(itms_escalation_data, oncall_escalation_data, [default_contact])

    except Exception as e:
        print "ERROR(lambda_handler): %s %s" % (type(e).__name__, e.args[0])

    return contacts
