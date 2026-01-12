#!/bin/bash
# Volume control with wpctl from WirePlumber
# Pass in "inc" argument to increase volume or pass in no arguments to decrement volume

inc="inc"
dec="dec"
mute="mute"

if [ "$1" == "$inc" ];then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+
elif [ "$1" == "$dec" ];then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
else
    wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
fi

