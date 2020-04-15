#!bin/bash
# Allow write permissions of /sys/class/backlight/{your_device}/brightness
# Pass in "inc" argument to increase brightness or pass in no arguments to decrement brightness

# Device -- change to your system device
device="intel_backlight"

# Brightness values
max_brightness=$(cat /sys/class/backlight/${device}/max_brightness)
current_brightness=$(cat /sys/class/backlight/${device}/brightness)

# 10% of max brightness
val=$(($max_brightness / 10))

# Increment and decrement
inc="inc"
dec="dec"

if [ "$1" == "$inc" ];then
    echo $(($current_brightness + $val)) > /sys/class/backlight/${device}/brightness;
else
    echo $(($current_brightness - $val)) > /sys/class/backlight/${device}/brightness;
fi
