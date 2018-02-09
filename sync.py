import json
import base64
import requests
import urllib.parse as urllib
import xml.etree.ElementTree as eTree
import lib
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from sys import exit


class Service:
    def __init__(self, settings):
        self.user = settings.attrib["user"]
        self.password = settings.attrib["password"]
        self.url = settings.attrib["url"]


class Atrium(Service):
    def __init__(self, settings):
        super().__init__(settings)
        headers = {
            'content-type': "application/x-www-form-urlencoded",
        }

        body = {
            'password': self.password,
            'username': self.user
        }

        url = "%s/api/jwt/login/" % self.url
        print('url: ', url)
        response = requests.request("POST", url, data=body, headers=headers)

        if response.status_code == 200:
            print('JWT auth response: ', response.text)
            self.access_token = response.text
        else:
            print(response.content)
            exit(0)

    def request(self, path, method, data=()):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.access_token
        }
        result = {}
        url = self.url + path
        if method == 'GET':
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == requests.codes.ok:
                result = json.loads(response.content.decode())
            else:
                print("ERROR %s - %s" % (response.status_code, response.text))
        elif method == 'POST':
            response = requests.post(
                url, 
                json.dumps(data), 
                headers=headers, 
                verify=False
            )
            if response.status_code == requests.codes.ok:
                result = json.loads(response.content.decode())
            else:
                print("ERROR %s - %s" % (response.status_code, response.text))
        return result


class Device42(Service):
    def request(self, path, method, data=(), doql=None):
        headers = {
            'Authorization': 'Basic ' + base64.b64encode((self.user + ':' + self.password).encode()).decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        result = None

        if method == 'GET':
            response = requests.get(self.url + path,
                                    headers=headers, verify=False)
            result = json.loads(response.content.decode())
        if method == 'POST' and doql is not None:
            payload = {
                "query": doql,
                "header": "yes"
            }
            response = requests.post(
                self.url + path,
                headers=headers,
                verify=False,
                data=payload
            )
            result = response.text
        return result


def init_services(settings):
    return {
        'atrium': Atrium(settings.find('atrium')),
        'device42': Device42(settings.find('device42'))
    }


def task_execute(task, services):
    print('Execute task:', task.attrib['description'])

    _resource = task.find('api/resource')
    _target = task.find('api/target')

    if _resource.attrib['target'] == 'atrium':
        resource_api = services['atrium']
        target_api = services['device42']
    else:
        resource_api = services['device42']
        target_api = services['atrium']

    mapping = task.find('mapping')
    source_url = _resource.attrib['path']

    method = _resource.attrib['method']
    doql = None

    if _resource.attrib.get("extra-filter"):
        source_url += _resource.attrib.get("extra-filter") + "&amp;"
    print(source_url)
    # sys.exit()
    if _resource.attrib.get('doql'):
        print(_resource.attrib['doql'])
        doql = _resource.attrib['doql']

    # source will contain the objects from the _resource endpoint
    if doql is not None:
        source = resource_api.request(source_url, method, doql=doql)
        lib.from_d42(
            source, mapping,
            _target, _resource,
            target_api, resource_api,
            doql=True
        )

    else:
        source = resource_api.request(source_url, method)
        lib.from_d42(
            source, mapping, 
            _target, _resource, 
            target_api, resource_api,
            doql=False
        )

print('Running...')

# Load mapping
config = eTree.parse('mapping.xml')
meta = config.getroot()

# Init transports services
services = init_services(meta.find('settings'))

# Parse tasks
tasks = meta.find('tasks')
for task in tasks:
    if task.attrib['enable'] == 'true':
        task_execute(task, services)
