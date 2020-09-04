*** Settings ***
Documentation  use FQDN to access app on openstack

Library  MexApp

Test Timeout   1 min 

*** Variables ***
${udp_fqdn}       server-ping-theaded3-udp.buckhorncluster.automationbuckhorncloudlet.gddt.mobiledgex.net
${tcp_fqdn}       localhost  #andyportstopk8s-tcp.automationfairviewcloudlet.gddt.mobiledgex.net
${http_fqdn}       my

${udp_port}   2016
${tcp_port}   2015
${http_port}  8080

${http_page}  xx

*** Test Cases ***
User shall be able to access port on openstack
    [Documentation]
    ...  deploy app with 1 UDP port
    ...  verify the port as accessible via fqdn

    #Egress Port Should Be Accessible  vm=cpc1598321065115894dkerprivplcy.dfwvmw2.packet.mobiledgex.net  host=35.199.188.102  protocol=tcp  port=2015

    Stop TCP Port  ${tcp_fqdn}  ${tcp_port}
    Start TCP Port  ${tcp_fqdn}   ${tcp_port}
#    Stop TCP Port  ${tcp_fqdn}  ${tcp_port}
    #UDP Port Should Be Alive  ${udp_fqdn}  ${udp_port}
    TCP Port Should Be Alive  ${tcp_fqdn}  ${tcp_port}  #tls=${True}
    #HTTP Port Should Be Alive  ${http_fqdn}  ${http_port}  ${http_page}

