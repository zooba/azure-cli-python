# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os
import requests
import time

from knack.log import get_logger

from .kudu import Kudu

STATIC_WEB_CONFIG = '''<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <remove name="PythonHandler" />
    </handlers>
  </system.webServer>
</configuration>'''

WEB_CONFIG = r'''<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <appSettings>
    <add key="PYTHONPATH" value="{home}"/>
    <add key="WSGI_HANDLER" value="{wsgi}"/>
    <add key="WSGI_LOG" value="D:\home\LogFiles\wfastcgi.log"/>
  </appSettings>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" scriptProcessor="{python}|{path}\wfastcgi.py" resourceType="Unspecified" requireAccess="Script"/>
    </handlers>
  </system.webServer>
</configuration>'''

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

    def collect_zip(self, source, version, wsgi_app):
        import io, zipfile

        source = os.path.abspath(source)

        py = self._get_py_info(version)
        py['home'] = self._home
        py['wsgi'] = wsgi_app

        binary_zip = io.BytesIO()
        with zipfile.ZipFile(binary_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('web.config', WEB_CONFIG.format(**py))

            for root, dirs, files in os.walk(source):
                # Non recursive for now
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d == '__pycache__']

                if os.path.split(root)[1] == 'static':
                    zf.writestr(
                        os.path.join(os.path.relpath(full, root), 'web.config'),
                        STATIC_WEB_CONFIG
                    )

                for f in files:
                    if f.startswith('.') or f.endswith('.pyc'):
                        continue
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, source)
                    zf.write(full, rel)

        return binary_zip


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
        self._kudu.exec_(py['python'] + ' -m pip ' + command, self._home)
        py['installed'] = self.pip_freeze(version)
        return py

    def pip_install_requirements(self, version):
        py = self._get_py_info(version)
        self._kudu.exec_(py['python'] + ' -m pip install -r requirements.txt', self._home)
        py['installed'] = self.pip_freeze(version)
        return py

    def pip_freeze(self, version):
        py = self._get_py_info(version)
        return self._kudu.exec_(py['python'] + ' -m pip freeze', self._home).splitlines()
