*** Settings ***
Documentation   Create new App
Library         MexConsole  url=%{AUTOMATION_CONSOLE_ADDRESS}
Library         MexMasterController  %{AUTOMATION_MC_ADDRESS}  %{AUTOMATION_MC_CERT}
Test Setup      Setup
Test Teardown   Close Browser

Test Timeout    40 minutes

*** Variables ***
${browser}           Chrome
${console_username}  mexadmin
${console_password}  mexadminfastedgecloudinfra
${developer_name}  MobiledgeX
${app_key}      -----BEGIN PUBLIC KEY-----${\n}MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Spdynjh+MPcziCH2Gij${\n}TkK9fspTH4onMtPTgxo+MQC+OZTwetvYFJjGV8jnYebtuvWWUCctYmt0SIPmA0F0${\n}VU6qzSlrBOKZ9yA7Rj3jSQtNrI5vfBIzK1wPDm7zuy5hytzauFupyfboXf4qS4uC${\n}GJCm9EOzUSCLRryyh7kTxa4cYHhhTTKNTTy06lc7YyxBsRsN/4jgxjjkxe3J0SfS${\n}z3eaHmfFn/GNwIAqy1dddTJSPugRkK7ZjFR+9+sscY9u1+F5QPwxa8vTB0U6hh1m${\n}QnhVd1d9osRwbyALfBY8R+gMgGgEBCPYpL3u5iSjgD6+n4d9RQS5zYRpeMJ1fX0C${\n}/QIDAQAB${\n}-----END PUBLIC KEY-----
${wait}  200

*** Test Cases ***
Web UI - User shall be able to create a New Kubernetes App for EU Region with Auth Public Key
    [Documentation]
    ...  Create a new EU Kubernetes App with Auth Public Key
    ...  Verify Kubernetes App shows in list

    Add New App  region=EU  app_name=${app_name}  developer_name=${developer_name}  deployment_type=kubernetes  access_ports=tcp:2015  auth_public_key=${app_key}

    App Should Exist  change_rows_per_page=True

    @{app_details}=    Show Apps  region=EU

    FOR  ${row}  IN  @{app_details}
        Run Keyword If  '${row['data']['key']['name']}' == '${app_name}'  Should Be Equal  ${row['data']['auth_public_key'].replace('\r\n', '\n')}  ${app_key.replace('\r\n', '\n')}
    END

    MexConsole.Delete App  click_previous_page=off

    App Should Not Exist


Web UI - User shall be able to create a New Docker App for EU Region with Auth Public Key
    [Documentation]
    ...  Create a new EU Docker App with Auth Public Key
    ...  Verify Docker App shows in list

    Add New App  region=EU  app_name=${app_name}  developer_name=${developer_name}  deployment_type=docker  access_ports=tcp:2015  auth_public_key=${app_key}

    App Should Exist  change_rows_per_page=True

    @{app_details}=    Show Apps  region=EU

    FOR  ${row}  IN  @{app_details}
        Run Keyword If  '${row['data']['key']['name']}' == '${app_name}'  Should Be Equal  ${row['data']['auth_public_key'].replace('\r\n', '\n')}  ${app_key.replace('\r\n', '\n')}
    END

    MexConsole.Delete App  click_previous_page=off

    App Should Not Exist

*** Keywords ***
Setup
    ${token}=  Get Supertoken
    ${app_name}=  Get Default App Name
    Open Browser
    Login to Mex Console  browser=${browser}  #username=${console_username}  password=${console_password}
    Open Compute
    Open Apps
    Set Suite Variable  ${token}
    Set Suite Variable  ${app_name}

Teardown
    Close Browser