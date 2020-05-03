#!/bin/bash
# Gets current wifi status

wifi_status=$(cat /sys/class/net/wlp3s0/carrier)
local_ip=$(ip addr | awk '/wlp3s0$/ {print $2}')

if (("$wifi_status" == 1));then
    echo "<span background='#008080'>  $local_ip <span foreground='#1b2631'></span></span>"
else
    echo "<span background='#008080'> 睊 <span foreground='#1b2631'></span></span>"
fi

