import uuid
import urlparse
import httplib
import socket
import ConfigParser

try:
    import simplejson as json
except ImportError:
    import json

def uuid_gen():
    return str(uuid.uuid1())

this_host = socket.gethostname()

service_ids = {}

def on_timer(options):
    config = ConfigParser.ConfigParser();
    config.read(options['conf'])

    defaults = dict(config.items('DEFAULT'))
    default_node_id = defaults.get('node.id', uuid_gen())
    default_node_environment = defaults.get('node.environment', "production")
    default_node_pool = defaults.get('node.pool', 'general')
    default_discovery_uri = defaults.get('discovery.uri')

    print 'zzzzz', defaults

    for section in config.sections():
        if section == 'DEFAULT':
            continue
        confs = dict(config.items(section))
  
        service_id = confs.get('id', service_ids.get(section, uuid_gen()))
        service_ids[section] = service_id
        node_id = confs.get('node.id', default_node_id)
        node_environment = confs.get('node.environment', default_node_environment)
        node_pool = confs.get('node.pool', default_node_pool)
        discovery_uri = confs.get('discovery.uri', default_discovery_uri)

        variables = globals().copy()
        variables.update(locals())
        #properties = dict([ k[9:], v%(variables) for k,v in conf.items() if k.startswith('property.') ])
        properties = dict([ (k[9:], v % variables) for (k,v) in confs.items() if k.startswith('property.') ])

        send(service_id, section, discovery_uri, node_id, node_environment, node_pool, properties)

def send(service_id, service_type, discovery_uri, node_id, node_environment, node_pool, properties):
    host, port = urlparse.urlparse(discovery_uri)[1].split(':')
    con = httplib.HTTPConnection(host, int(port), timeout=120)
    headers = {
        'content-type': 'application/json',
        'user-agent': 'presto-python-announcer'
    }

    data = {
        'environment': node_environment,
        'node_id': node_id,
        'location': '/%s' % node_id,
        'pool': node_pool,
        'services': [
            {
                'id': service_id,
                'type': service_type,
                'properties': properties
            }
        ]
    }

    body = json.dumps(data)
    print (node_id, body)

    url = '/v1/announcement/%s' % node_id
    try:
        con.request('PUT', url, body, headers)
        response = con.getresponse()
    except Exception as e:
        print e
        return

    if response.status >= 400:
        print response.status, url, response.read()
    else:
        print response.status, url, body
