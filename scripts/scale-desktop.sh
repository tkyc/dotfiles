#!/bin/bash
    
# Scale desktop
output=$(wlr-randr | sed -n '1p' | awk '{print $1}')
wlr-randr --output $output --scale 1.25

