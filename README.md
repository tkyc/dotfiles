#Personal auto rice for i3wm environment -- always a WIP

Create "Scripts" folder in home directory and place scripts from repo in there
All scripts are execute only, so edits require permission changes

1. Setup wifi
    - wireless_tools, dhclient, wpa_supplicant
    - set network conf file in /etc/wpa_supplicant.conf

2. Setup vim
    - fzf and ripgrep

3. Setup system fonts
    - /etc/fonts/local.conf
    - Install some fonts
        - sudo pacman -S ttf-dejavu ttf-liberation noto-fonts (for web browser)
        - Get Inconsolata and Noto nerd fonts from AUR for URXVT (nerd-fonts-inconsolata and nerd-fonts-noto)
    - Enable font presets
        - sudo ln -s /etc/fonts/conf.avail/70-no-bitmaps.conf /etc/fonts/conf.d
        - sudo ln -s /etc/fonts/conf.avail/10-sub-pixel-rgb.conf /etc/fonts/conf.d
        - sudo ln -s /etc/fonts/conf.avail/11-lcdfilter-default.conf /etc/fonts/conf.d
    - Uncomment mode at end
        - vim /etc/profile.d/freetype2.sh
        - export FREETYPE_PROPERTIES="truetype:interpreter-version=40"
