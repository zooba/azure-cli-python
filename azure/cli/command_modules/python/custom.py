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


def publish_to_webapp(cmd, resource_group_name, name, slot=None, source='.',
                      version='364x64', wsgi='app.application'):
    app = _get_app(cmd, resource_group_name, name, slot)
    app.install_python(version)

    data = app.collect_zip(source, version, wsgi)
    app.deploy_zip(data)
    return app.pip_install_requirements(version)


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
