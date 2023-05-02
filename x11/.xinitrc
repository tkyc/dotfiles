# All settings must be set before start of window manager

# Sets background
feh --bg-scale $BACKGROUND

# Sets terminal settings
xrdb -load ~/.Xdefaults


# Disable screen saver
xset s off
xset -dpms
xset s noblank

# Fix for flatpak as it depends on xdg-desktop-portal -- https://github.com/flatpak/xdg-desktop-portal-gtk/issues/72
dbus-update-activation-environment --systemd DBUS_SESSION_BUS_ADDRESS DISPLAY XAUTHORITY

# Start window manager
exec dwm

