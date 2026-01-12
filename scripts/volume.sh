#!/bin/bash
# Volume control with wpctl from WirePlumber
# Pass in "inc" argument to increase volume or pass in no arguments to decrement volume

inc="i"
dec="d"
mute="m"
print="p"

if [ "$1" == "$inc" ];then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+
elif [ "$1" == "$dec" ];then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
elif [ "$1" == "$print" ];then
    wpctl get-volume @DEFAULT_AUDIO_SINK@
elif [ "$1" == "$mute" ];then
    wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
fi

