#
# ~/.bashrc
#

# Personal shell scripts
export PATH=$PATH:/home/$USER/repo/dotfiles/scripts

# Java
export JAVA_HOME=/home/$USER/java/jdk-25
export PATH=/home/$USER/java/jdk-25/bin:$PATH
export PATH=/home/$USER/java/mvn/bin:$PATH

# Terminal prompt display -- configure what is displayed on terminal prompt ex. directory, git branch, etc...
colour='\[\e[36m\]'
no_colour='\[\e[0m\]'
alias ls='ls --color=auto'

parse_git_branch() {
     git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

# 
export PS1="[\u@\h \[\e[32m\]\w\[\e[91m\]\$(parse_git_branch)\[\e[00m\] ${colour}${no_colour}] "

