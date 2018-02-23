# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['python'] = """
type: group
short-summary: Manage Python resources on Azure.
"""

helps['python webapp'] = """
type: group
short-summary: Manage Python web apps.
"""

helps['python webapp deploy'] = """
    type: command
    short-summary: Deploy a Python project to a web app.
    examples:
    - name: Enable AAD by enabling authentication and setting AAD-associated parameters. Default provider is set to AAD. Must have created a AAD service principal beforehand.
      text: >
        az webapp auth update  -g myResourceGroup -n myUniqueApp --enabled true \\
          --action LoginWithAzureActiveDirectory \\
          --aad-allowed-token-audiences https://webapp_name.azurewebsites.net/.auth/login/aad/callback \\
          --aad-client-id ecbacb08-df8b-450d-82b3-3fced03f2b27 --aad-client-secret very_secret_password \\
          --aad-token-issuer-url https://sts.windows.net/54826b22-38d6-4fb2-bad9-b7983a3e9c5a/
    - name: Allow Facebook authentication by setting FB-associated parameters and turning on public-profile and email scopes; allow anonymous users
      text: >
        az webapp auth update -g myResourceGroup -n myUniqueApp --action AllowAnonymous \\
          --facebook-app-id my_fb_id --facebook-app-secret my_fb_secret \\
          --facebook-oauth-scopes public_profile email
"""
