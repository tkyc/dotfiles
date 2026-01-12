#
# ~/.bashrc
#

# Personal shell scripts
export PATH=$PATH:/home/tkyc/Scripts

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
