#!/bin/bash

systemctl --user enable pipewire.service pipewire-pulse.socket
systemctl --user start pipewire.service pipewire-pulse.socket

