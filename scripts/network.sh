#!/bin/bash
# Gets current wifi status

#wifi_status=$(cat /sys/class/net/wlp3s0/carrier)
local_ip=$(ip addr | awk '/wlp3s0$/ {print $2}')

#if (("$wifi_status" == 1));then
if [ ! -z $local_ip ];then
#    echo "<span background='#4b846c'>  $local_ip <span foreground='#1b2631'></span></span>"
    echo "<span background='#4b846c'><span background='#0F9D58'>  </span> $local_ip </span>"
else
    local_ip=$(ip addr | awk '/enp0s3$/ {print $2}')

    if [ ! -z $local_ip ];then
        echo "<span background='#4b846c'><span background='#0F9D58'>  </span> $local_ip </span>"
    else
        echo "<span background='#4b846c'><span background='#0F9D58'>  </span> Disconnected </span>"
    fi
fi


