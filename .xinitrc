# Sets background
feh --bg-scale ~/Folder/backgrounds/00.jpg

# Sets terminal settings
xrdb -load ~/.Xdefaults

# Disable screen saver
xset s off
xset -dpms
xset s noblank

# Start window manager
exec dwm
