#!/bin/bash
# Tmux pane setup

# Default-----------------------------------------

# Flags
p_flag="-p"

tmux rename-window -t 0 "CodeEditor []"

if [[ "$1" == "$p_flag" ]]; then
    tmux split-window -h
    tmux select-pane -t 1
    tmux resize-pane -x 50
    tmux select-pane -t 0
else
    tmux new-window
    tmux rename-window -t 1 "Shell "
    tmux select-window -t 0

fi

nvim .

#-------------------------------------------------

# 2 panes horizontal
#tmux split-window -v
#tmux resize-pane -y 8
#tmux select-pane -t 0

# 3 panes horizontal
#tmux split-window -v
#tmux split-window -h
#tmux resize-pane -y 9
#tmux select-pane -t 0
