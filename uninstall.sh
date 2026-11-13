#!/bin/sh
# Remove the `piazza` launcher. Your chats/config in ~/.config/nchat and this directory are left alone.
set -eu
rm -f "$HOME/.local/bin/piazza"
echo "launcher removed. To undo the kitty mappings, delete the 'piazza:' lines in ~/.config/kitty/kitty.conf."
