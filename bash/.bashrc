# Functions --------------------------------------------------------------------------------------------

# Gets current branch
parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

# Launch tmux when terminal opens
auto_start_tmux() {
    if [[ $DISPLAY ]]; then
        # If not running interactively, do not do anything
        [[ $- != *i* ]] && return
        [[ -z "$TMUX" ]] && exec tmux
    fi
}

auto_start_tmux

#--------------------------------------------------------------------------------------------------------



# General -----------------------------------------------------------------------------------------------

# Personal shell scripts
export PATH=$PATH:/home/tkyc/Scripts

# Enable fzf to search hidden directories/files
export FZF_DEFAULT_COMMAND="find -L"

# JAVA_HOME
export JAVA_HOME=~/Folder/jdk/jdk-19
PATH=$JAVA_HOME/bin:$PATH

# Path to current background
export BACKGROUND=~/Folder/backgrounds/bg8.png

# For running Intellij
export _JAVA_AWT_WM_NONREPARENTING=1

# Flutter
export PATH="/opt/flutter/bin:$PATH"

# Autocomplete shell commands after "sudo"
complete -cf sudo

#--------------------------------------------------------------------------------------------------------



# Terminal prompt display -------------------------------------------------------------------------------

colour='\[\e[91m\]'
no_colour='\[\e[0m\]'
alias ls='ls --color=auto'

# Default terminal prompt display
ps1='[\u@\h \W] '

if pgrep -x "dwm" > /dev/null; then
    ps1="[\u@\h \[\e[91m\]\w\[\e[36m\]\$(parse_git_branch)\[\e[00m\] ${colour}${no_colour}] " # ,36m,91m
fi

export PS1=$ps1

#--------------------------------------------------------------------------------------------------------

