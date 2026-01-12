#!/bin/bash
# Updates the dotfiles by copying them over
# Execute this script in the scripts directory of this repo

user=$USER
if [ ! -z $SUDO_USER ]
then
    user=$SUDO_USER
fi

# Update scripts
cp /home/$user/scripts/* .

# Update dotfiles
cp /home/$user/.bashrc /home/$user/repo/dotfiles/bash/
cp /home/$user/.vimrc /home/$user/repo/dotfiles/nvim/
cp /home/$user/.config/nvim/init.lua /home/$user/repo/dotfiles/nvim/

