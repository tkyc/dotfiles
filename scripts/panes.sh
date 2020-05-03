#!/bin/bash
# Tmux pane setup

# 2 windows
tmux rename-window Editor
tmux new-window
tmux select-window -t 0

# 2 panes
#tmux split-window -v
#tmux resize-pane -y 8
#tmux select-pane -t 0

# 3 panes
#tmux split-window -v
#tmux split-window -h
#tmux resize-pane -y 9
#tmux select-pane -t 0
