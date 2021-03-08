#!/bin/bash
# Kills the current tmux session

#session=$(tmux display-message -p "#S")
#tmux kill-session -t "$session"
tmux kill-session -t $(tmux display-message -p "#S")
