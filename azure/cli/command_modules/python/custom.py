# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import requests

from knack.log import get_logger

from .windowswebapp import WindowsWebapp

logger = get_logger(__name__)

def _get_app(cmd, resource_group_name, name, slot=None):
    return WindowsWebapp(cmd, resource_group_name, name, slot)


def _collect_zip(source):
    import io, zipfile, os
    
    source = os.path.abspath(source)
    ignore_dir = []
    try:
        with open(os.path.join(source, '.gitignore'), 'r') as f:
            ignore_dir = [line.rstrip(' \r\n') for line in f if not line.strip().startswith('#')]
        ignore_dir = set(d.rstrip('/\\') for d in ignore_dir if d.endswith(('/', '\\')))
    except:
        pass

    binary_zip = io.BytesIO()
    with zipfile.ZipFile(binary_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source):
            # Non recursive for now
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            dirs[:] = [d for d in dirs if d not in ignore_dir]
            
            for f in files:
                if f.startswith('.'):
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, source)
                zf.write(full, rel)
    return binary_zip


def publish_to_webapp(cmd, resource_group_name, name, slot=None, source='.'):
    app = _get_app(cmd, resource_group_name, name, slot)

    data = _collect_zip(source)
    app.deploy_zip(data)


def install_to_webapp(cmd, resource_group_name, name, slot=None, version='364x64'):
    app = _get_app(cmd, resource_group_name, name, slot)
    return app.install_python(version)


def uninstall_from_webapp(cmd, resource_group_name, name, slot=None, version=None):
    app = _get_app(cmd, resource_group_name, name, slot)
    if not version:
        version = app.list_python()[0]
    return app.uninstall_python(version)


def show_webapp_info(cmd, resource_group_name, name, slot=None):
    app = _get_app(cmd, resource_group_name, name, slot)
    res = []
    for py_data in app.list_python():
        try:
            py_data['installed'] = app.pip_freeze(py_data)
        except RuntimeError as ex:
            py_data['installed'] = []
            py_data['path'] = ''
            py_data['error'] = str(ex)

        res.append(py_data)

    return res
