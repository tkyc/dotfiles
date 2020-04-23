#!/bin/bash
# Gets current wifi status

wifi_status=$(cat /sys/class/net/wlp3s0/carrier)

if (("$wifi_status" == 1));then
    echo "<span background='#008080'>  </span>"
fi

echo "<span background='#008080'> 睊 </span>"
