from lib.common import conf
import urllib2
import httplib
import json
import base64
import copy

class ApiRequest():

    def __init__(self):
        self._req_type = None
        self._path = None
        self._content = None
        self._headers = {'Content-type': 'application/json'}
        self._domain = conf.properties['main.server.hostname']
        self.simpleAuth(conf.properties['foreman.admin.username'],
                        conf.properties['foreman.admin.password'])

    def simpleAuth(self,name,password):
        self._headers['Authorization'] = 'Basic %s' % base64.b64encode(name+":"+password)
        return copy.deepcopy(self)

    def path(self,change):
        self._path = change
        return copy.deepcopy(self)

    def content(self,change):
        self._content = change
        return copy.deepcopy(self)
    
    def header(self,name,value):
        self._headers[name] = value
        return copy.deepcopy(self)

    def domain(self,change):
        self._domain = change
        return copy.deepcopy(self)

    def submit(self):
        connection = httplib.HTTPSConnection(self._domain)
        json_content = ""
        if self._content:
            json_content = json.dumps(self._content)
        connection.request(self._req_type, self._path, json_content, self._headers)
        response = connection.getresponse()
        outstring = response.read().decode()
        try: 
            return json.loads(outstring)
        except ValueError:
            return outstring

    def get(self):
        self._req_type = 'GET'
        return copy.deepcopy(self)

    def post(self):
        self._req_type = 'POST'
        return copy.deepcopy(self)

    def put(self):
        self._req_type = 'PUT'
        return copy.deepcopy(self)

    def delete(self):
        self._req_type = 'DELETE'
        return copy.deepcopy(self)
