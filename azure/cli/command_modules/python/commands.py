# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.core.util import empty_on_404

from ._client_factory import cf_web_client, cf_plans, cf_webapps


def output_slots_in_table(slots):
    return [{'name': s['name'], 'status': s['state'], 'plan': s['appServicePlan']} for s in slots]


def transform_list_location_output(result):
    return [{'name': x.name} for x in result]


def transform_web_output(web):
    props = ['name', 'state', 'location', 'resourceGroup', 'defaultHostName', 'appServicePlanId', 'ftpPublishingUrl']
    result = {k: web[k] for k in web if k in props}
    # to get width under control, also the plan usually is in the same RG
    result['appServicePlan'] = result.pop('appServicePlanId').split('/')[-1]
    return result


def transform_web_list_output(webs):
    return [transform_web_output(w) for w in webs]


def ex_handler_factory(creating_plan=False):
    def _polish_bad_errors(ex):
        import json
        from knack.util import CLIError
        try:
            detail = json.loads(ex.response.text)['Message']
            if creating_plan:
                if 'Requested features are not supported in region' in detail:
                    detail = ("Plan with linux worker is not supported in current region. For " +
                              "supported regions, please refer to https://docs.microsoft.com/en-us/"
                              "azure/app-service-web/app-service-linux-intro")
                elif 'Not enough available reserved instance servers to satisfy' in detail:
                    detail = ("Plan with Linux worker can only be created in a group " +
                              "which has never contained a Windows worker, and vice versa. " +
                              "Please use a new resource group. Original error:" + detail)
            ex = CLIError(detail)
        except Exception:  # pylint: disable=broad-except
            pass
        raise ex
    return _polish_bad_errors


# pylint: disable=too-many-statements
def load_command_table(self, _):
    webapp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.web.operations.web_apps_operations#WebAppsOperations.{}',
        client_factory=cf_webapps
    )
    with self.command_group('python webapp', webapp_sdk) as g:
        g.custom_command('publish', 'publish_to_webapp')
        g.custom_command('install', 'install_to_webapp')
        g.custom_command('uninstall', 'uninstall_from_webapp')
        g.custom_command('show', 'show_webapp_info')

    with self.command_group('python functionapp') as g:
        g.custom_command('publish', 'publish_to_functionapp')
        g.custom_command('install', 'install_to_functionapp')
        g.custom_command('uninstall', 'uninstall_from_functionapp')
        g.custom_command('show', 'show_functionapp_info')
