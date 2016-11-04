# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
from json import dumps

auth = ('admin', 'changeme')

url = 'https://ibm-x3550m3-08.lab.eng.brq.redhat.com/api/v2/config_templates' \
      '/185'
print(requests.get(url, auth=auth, verify=False).json())


headers = {'content-type': 'application/json'}
print(requests.put(
    url,
    data=dumps({
        'config_template':
            {
                'template_combinations_attributes': [
                    {'hostgroup_id': 2, 'environment_id': 2}
                ]
            }
    }),
    auth=auth,
    verify=False,
    headers=headers).json())


