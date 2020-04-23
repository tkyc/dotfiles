#!/bin/bash
# Get the amount of memory currently being used

used_memory=$(free -h | grep Mem | awk '{print $3}')
echo "<span background='#008080'> $used_memory </span>"
