#!/bin/bash
# Updates the dotfiles by copying them over
# Execute this script in the scripts directory of this repo

# Update scripts
cp ~/scripts/* .

# Update dotfiles
cp ~/.bash_profile ../
cp ~/.bashrc ../
cp ~/.config/i3/config ../
cp ~/.config/i3status/i3status.conf ../
cp ~/.tmux.conf ../
cp ~/.vimrc ../
cp ~/.Xdefaults ../
cp ~/.xinitrc ../
