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
cp /home/$user/.config/i3/config ../
cp /home/$user/.config/gtk-3.0/settings.ini ../
cp /home/$user/.tmux.conf ../
cp /home/$user/.vimrc ../
cp /home/$user/.vim/colors/profile.vim ../
cp /home/$user/.config/nvim/init.vim ../
cp /home/$user/.config/nvim/coc.vim ../
cp /home/$user/.Xdefaults ../
cp /home/$user/.xinitrc ../

