# Sets background
feh --bg-scale ~/Folder/backgrounds/101.png

# Sets terminal settings
xrdb -load ~/.Xdefaults

# Disable screen saver
xset s off
xset -dpms
xset s noblank

# Start window manager
exec dwm
