#!/bin/bash
# Get the amount of memory currently being used

used_memory=$(free -h | grep Mem | awk '{print $3}')
#echo "<span background='#4b846c'><span background='#EA4335'>  </span> $used_memory </span>"
echo "<span background='#C7607A'>  $used_memory Plied </span>"
