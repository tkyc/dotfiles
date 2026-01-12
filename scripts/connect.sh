#!/bin/bash
# Edit /etc/wpa_supplicant.conf file to specify network
# File is contents is of the following form:
#
# network={
#    ssid="your_ssid"
#    psk="ssid_pass"
# }
#
# Use the following command to scan for networks:
# sudo iwlist wlan0 scan
#
# Use the following command to list network cards:
# sudo ip addr

sudo ip link wlp3s0 set up
sudo wpa_supplicant -B -i wlp3s0 -c /etc/wpa_supplicant.conf
sudo dhclient wlp3s0

