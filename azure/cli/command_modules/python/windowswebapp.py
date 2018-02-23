# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import requests
import time

from knack.log import get_logger

from .kudu import Kudu

logger = get_logger(__name__)

class WindowsWebapp(object):
    def __init__(self, cmd, resource_group_name, name, slot):
        self._kudu = Kudu(cmd, resource_group_name, name, slot)
        self._home = 'D:\\home\\site\\wwwroot'

    def _get_py_info(self, data):
        if isinstance(data, dict):
            data = data.get('package') or data.get('id')
        if not data.lower().startswith('python'):
            data = 'python' + data

        path = "D:\\home\\" + ("Python27" if data.lower().startswith('python27') else data)
        return {
            'package': data,
            'path': path,
            'python': path + '\\python.exe',
        }

    def install_python(self, version):
        py = self._get_py_info(version)['package']
        self._kudu.put('siteextensions/' + py)
        return py

    def list_python(self):
        return [self._get_py_info(d) for d in self._kudu.get('siteextensions?filter=python')]

    def uninstall_python(self, version):
        self._kudu.delete('siteextensions/' + self._get_py_info(version)['package'])

    def deploy_zip(self, zip_data):
        r = self._kudu._post('zipdeploy?isAsync=true', data=zip_data.getbuffer())
        status_url = r.headers['Location']

        while True:
            time.sleep(1.0)
            r = self._kudu._session.get(status_url)
            r.raise_for_status()
            res = r.json()
            if res['complete']:
                break
            # TODO: Check error and raise

    def pip_install(self, version, command):
        py = self._get_py_info(version)
        self._kudu.exec_(py['python'] + ' -m pip -y ' + command, self._home)
        py['installed'] = self.pip_freeze(version)
        return py

    def pip_install_requirements(self, version):
        py = self._get_py_info(version)
        self._kudu.exec_(py['python'] + ' -m pip -y install -r requirements.txt', self._home)
        py['installed'] = self.pip_freeze(version)
        return py

    def pip_freeze(self, version):
        py = self._get_py_info(version)
        return self._kudu.exec_(py['python'] + ' -m pip freeze', self._home).splitlines()
