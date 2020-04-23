#!/bin/bash
# Gets current wifi status

wifi_status=$(cat /sys/class/net/wlp3s0/carrier)
local_ip=$(ip addr | awk 'FNR == 11 {print $2}')

if (("$wifi_status" == 1));then
    echo "<span background='#008080'>  $local_ip </span>"
fi

echo "<span background='#008080'> 睊 </span>"
