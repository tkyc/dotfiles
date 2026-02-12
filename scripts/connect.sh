#!/bin/bash
#
# To enable, add the configuration below to /etc/iwd/main.conf
#
# [General]
# EnableNetworkConfiguration=true
#
# For 8021x APs, create a file with the contents below
# with the .8021x extension eg. your-ssid.8021.x in
# the directory /var/lib/iwd/
#
# [Security]
# EAP-Method=PEAP
# EAP-Identity=anonymous
# EAP-PEAP-Phase2-Method=MSCHAPV2
# EAP-PEAP-Phase2-Identity=<username>
# EAP-PEAP-Phase2-Password=<password>
# 
# [Settings]
# AutoConnect=true
#

echo "sudo iwctl known-networks list"
echo "sudo iwctl known-networks <SSID> forget"
echo "sudo iwctl device list"
echo "sudo iwctl station <adapter> scan"
echo "sudo iwctl station <adapter> get-networks"
echo "sudo iwctl station <adapter> connect <SSID>"

