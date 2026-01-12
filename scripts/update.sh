#!/bin/bash
# Updates the dotfiles by copying them over
# Execute this script in the scripts directory of this repo

user=$USER
if [ ! -z $SUDO_USER ]
then
    user=$SUDO_USER
fi

# Update scripts
cp /home/$user/Scripts/* .

# Update dotfiles
cp /home/$user/.bash_profile ../
cp /home/$user/.bashrc ../
cp /home/$user/.vimrc ../
cp /home/$user/.config/nvim/init.lua ../

