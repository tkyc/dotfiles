#!/bin/bash
# Updates the dotfiles by copying them to dotfiles project

user=$USER
if [ ! -z $SUDO_USER ]
then
    user=$SUDO_USER
fi

# Update scripts
cp /home/$user/Scripts/* /home/$user/Repos/dotfiles/scripts

# Update dotfiles
cp /home/$user/.bash_profile /home/$user/Repos/dotfiles/bash
cp /home/$user/.bashrc /home/$user/Repos/dotfiles/bash
cp /home/$user/.config/gtk-3.0/settings.ini /home/$user/Repos/dotfiles/gtk
cp /home/$user/.tmux.conf /home/$user/Repos/dotfiles/tmux
cp /home/$user/.vimrc /home/$user/Repos/dotfiles/nvim
cp /home/$user/.vim/colors/profile.vim /home/$user/Repos/dotfiles/nvim
cp /home/$user/.config/nvim/init.vim /home/$user/Repos/dotfiles/nvim
cp /home/$user/.config/nvim/coc.vim /home/$user/Repos/dotfiles/nvim
cp /home/$user/.Xdefaults /home/$user/Repos/dotfiles/x11
cp /home/$user/.xinitrc /home/$user/Repos/dotfiles/x11

