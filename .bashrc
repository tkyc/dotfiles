#
# ~/.bashrc
#

# Personal shell scripts
export PATH=$PATH:/home/tkyc/Scripts

# Intellij
export PATH=$PATH:/bin/idea

# JAVA_HOME
# export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export JAVA_HOME=/usr/lib/jvm/java-16-openjdk/jdk-16.0.1

export PATH=$PATH:$HOME/.local/bin

# mssql server jdbc test connection string
export mssql_jdbc_test_connection_properties="jdbc:sqlserver://0.0.0.0:1433;user=sa;password=;"

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

# Terminal prompt display -- configure what is displayed on terminal prompt ex. directory, git branch, etc...
colour='\[\e[36m\]'
no_colour='\[\e[0m\]'
alias ls='ls --color=auto'

parse_git_branch() {
     git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

#export PS1='[\u@\h \W]\$ '

# 
export PS1="[\u@\h \[\e[32m\]\w\[\e[91m\]\$(parse_git_branch)\[\e[00m\] ${colour}${no_colour}] "
