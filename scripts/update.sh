#!/bin/bash
# Updates the dotfiles by copying them over
# Execute this script in the scripts directory of this repo

user=$USER
if [ ! -z $SUDO_USER ]
then
    user=$SUDO_USER
fi

# Update dotfiles in system
update="u"
if [ "$1" == "$update" ];then
    cp /home/$user/repo/dotfiles/bash/.bashrc /home/$user/
    cp -r /home/$user/repo/dotfiles/nvim/ /home/$user/.config/
    cp /home/$user/repo/dotfiles/foot/foot.ini /home/$user/.config/foot/
    cp /home/$user/repo/dotfiles/tmux/.tmux.conf /home/$user/
fi

# Update dotfiles in repo
cp /home/$user/.bashrc /home/$user/repo/dotfiles/bash/
cp -r /home/$user/.config/nvim/ /home/$user/repo/dotfiles/
cp /home/$user/.config/foot/foot.ini /home/$user/repo/dotfiles/foot/
cp /home/$user/.tmux.conf /home/$user/repo/dotfiles/tmux/

