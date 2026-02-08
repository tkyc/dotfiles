#!/bin/bash
# Clears the buf/cache

echo 3 | sudo tee /proc/sys/vm/drop_caches
echo "Cleared!"

