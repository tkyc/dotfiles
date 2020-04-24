#!/bin/bash
# Tmux pane setup

tmux split-window -v
tmux split-window -h
tmux resize-pane -y 9
tmux select-pane -t 0
