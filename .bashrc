#
# ~/.bashrc
#

export PATH=$PATH:/home/tkyc/Scripts

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# Launch tmux when terminal opens
if [[ $DISPLAY ]]; then
    # If not running interactively, do not do anything
    [[ $- != *i* ]] && return
    [[ -z "$TMUX" ]] && exec tmux
fi

# Attach back to previous tmux session
#if [[ -z "$TMUX" ]] ;then
#    ID="$( tmux ls | grep -vm1 attached | cut -d: -f1 )" # get the id of a deattached session
#    if [[ -z "$ID" ]] ;then # if not available create a new one
#        tmux new-session
#    else
#        tmux attach-session -t "$ID" # if available attach to it
#    fi
#fi

alias ls='ls --color=auto'
PS1='[\u@\h \W]\$ '
