#!/bin/bash
# Updates the dotfiles by copying them to dotfiles project

user=$USER
if [ ! -z $SUDO_USER ]
then
    user=$SUDO_USER
fi

# Update scripts
cp /home/$user/Scripts/* /home/$user/Repos/auto_rice_dotfiles/scripts

# Update dotfiles
cp /home/$user/.bash_profile /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.bashrc /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.config/gtk-3.0/settings.ini /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.tmux.conf /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.vimrc /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.vim/colors/profile.vim /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.config/nvim/init.vim /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.config/nvim/coc.vim /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.Xdefaults /home/$user/Repos/auto_rice_dotfiles
cp /home/$user/.xinitrc /home/$user/Repos/auto_rice_dotfiles

