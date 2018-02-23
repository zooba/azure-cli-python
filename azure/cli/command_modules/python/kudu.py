# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import requests

from knack.log import get_logger

from ..appservice._appservice_utils import _generic_site_operation

logger = get_logger(__name__)

class Kudu(object):
    def __init__(self, cmd, resource_group_name, name, slot):
        url, user, pwd = self._get_details(cmd, resource_group_name, name, slot)
        self._api_url = 'https://' + url + '/api/'
        self._session = requests.Session()
        self._session.auth = user, pwd

    @classmethod
    def _get_details(cls, cmd, resource_group_name, name, slot):
        import xmltodict

        content = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                          'list_publishing_profile_xml_with_secrets', slot)
        full_xml = ''
        for f in content:
            full_xml += f.decode()

        profiles = xmltodict.parse(full_xml, xml_attribs=True)['publishData']['publishProfile']
        profile = next((p for p in profiles if p.get('@publishMethod') == 'MSDeploy'), {})
        return profile.get('@publishUrl'), profile.get('@userName'), profile.get('@userPWD')

    def _get(self, path):
        r = self._session.get(self._api_url + path)
        r.raise_for_status()
        return r

    def _put(self, path):
        r = self._session.put(self._api_url + path)
        r.raise_for_status()
        return r

    def _post(self, path, json=None, data=None):
        r = self._session.post(self._api_url + path, json=json, data=data)
        r.raise_for_status()
        return r

    def _delete(self, path):
        r = self._session.delete(self._api_url + path)
        r.raise_for_status()
        return r

    def get(self, path):
        return self._get(path).json()

    def put(self, path):
        return self._get(path).json()

    def post(self, path, body):
        data, json = None, None
        if isinstance(body, (dict, list)):
            json = body
        if isinstance(data, (bytes, str)):
            data = body
        return self._post(path, json, data).json()

    def delete(self, path):
        self._delete(path)

    def exec_(self, cmd, cwd):
        r = self.post('command', { 'command': cmd, 'dir': cwd })
        try:
            ec = int(r.get('ExitCode'))
        except ValueError:
            ec = -1
        if ec == 0:
            return r.get('Output', '')
        raise RuntimeError(r.get('Error'))
