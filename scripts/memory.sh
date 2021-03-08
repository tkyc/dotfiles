#!/bin/bash
# Get the amount of memory currently being used

used_memory=$(free -h | grep Mem | awk '{print $3}')
echo "<span background='#4b846c'><span background='#008b8b'>  </span> $used_memory </span>"
