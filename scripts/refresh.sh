#!/bin/bash
# Kills stale processes, execute only if no windows besides terminal is open

pkill -f pulseaudio
pkill -f xfconfd
pkill -f at-spi2-registryd

