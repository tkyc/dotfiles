#!/bin/bash
# Gets the current battery life in percentage
# Percentage is saved in .uevent in home directory

#while true
#do
#    BAT0_MAX=$(cat /sys/class/power_supply/BAT0/uevent | grep FULL= | tr -d -c 0-9)
#
#    BAT1_MAX=$(cat /sys/class/power_supply/BAT1/uevent | grep FULL= | tr -d -c 0-9)
#    
#    BAT_MAX=$(($BAT0_MAX + $BAT1_MAX))
#    
#    BAT0_NOW=$(cat /sys/class/power_supply/BAT0/uevent | grep ENERGY_NOW | tr -d -c 0-9)
#    
#    BAT1_NOW=$(cat /sys/class/power_supply/BAT1/uevent | grep ENERGY_NOW | tr -d -c 0-9)
#    
#    BAT_NOW=$(($BAT0_NOW + $BAT1_NOW))
#
#    echo $((100 * BAT_NOW / BAT_MAX)) > ~/.uevent
#
#    sleep 600
#done

BAT0_MAX=$(cat /sys/class/power_supply/BAT0/uevent | grep FULL= | tr -d -c 0-9)

BAT1_MAX=$(cat /sys/class/power_supply/BAT1/uevent | grep FULL= | tr -d -c 0-9)

BAT_MAX=$(($BAT0_MAX + $BAT1_MAX))

BAT0_NOW=$(cat /sys/class/power_supply/BAT0/uevent | grep ENERGY_NOW | tr -d -c 0-9)

BAT1_NOW=$(cat /sys/class/power_supply/BAT1/uevent | grep ENERGY_NOW | tr -d -c 0-9)

BAT_NOW=$(($BAT0_NOW + $BAT1_NOW))

echo $((100 * BAT_NOW / BAT_MAX))
