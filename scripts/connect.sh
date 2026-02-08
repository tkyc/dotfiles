#!/bin/bash
#
# Add the configuration below to /etc/iwd/main.conf
#
# [General]
# EnableNetworkConfiguration=true
#

echo "sudo iwctl known-networks list"
echo "sudo iwctl known-networks <SSID> forget"
echo "sudo iwctl station device list"
echo "sudo iwctl station <adapter> get-networks"
echo "sudo iwctl station <adapter> connect <SSID>"

