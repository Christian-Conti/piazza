#!/bin/sh
# piazza installer: fetches nchat (submodule), applies the piazza patch, builds, installs the `piazza` launcher.
#   ./install.sh                  build + install launcher + point nchat at the image/GIF preview script
#   ./install.sh --kitty          also append the Shift+Enter / Ctrl+M mappings to ~/.config/kitty/kitty.conf
#   ./install.sh --reset-config   back up key.conf and color.conf so the new defaults apply
set -eu

ROOT="$(cd "$(dirname "$0")" && pwd)"
CONF="${HOME}/.config/nchat"
KITTY=0
RESET=0
for arg in "$@"; do
  case "$arg" in
    --kitty) KITTY=1 ;;
    --reset-config) RESET=1 ;;
    *) echo "unknown option: $arg"; exit 1 ;;
  esac
done

missing=""
for tool in git cmake ninja go gperf patch make c++; do
  command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done
if [ -n "$missing" ]; then
  echo "missing tools:$missing"
  echo "Debian/Ubuntu: sudo apt install -y build-essential cmake ninja-build gperf golang git patch ccache help2man \\"
  echo "  libreadline-dev libssl-dev libncurses-dev libncursesw5-dev zlib1g-dev libsqlite3-dev libmagic-dev libcurl4-openssl-dev"
  exit 1
fi

# 1. nchat source: submodule when this is a git checkout, otherwise it ships next to this script
if [ -d "$ROOT/.git" ]; then
  git -C "$ROOT" submodule update --init
fi

# 2. apply the piazza patch once
if [ ! -f "$ROOT/nchat/.piazza-applied" ]; then
  patch -p1 -d "$ROOT/nchat" < "$ROOT/patches/0001-piazza.patch"
  touch "$ROOT/nchat/.piazza-applied"
fi

# 3. build (first build compiles tdlib for Telegram: expect 15-30 minutes)
cmake -S "$ROOT/nchat" -B "$ROOT/nchat/build" -G Ninja -DHAS_TESTS=OFF -DCMAKE_BUILD_TYPE=Release
# all targets: nchat plus the protocol plugins (libtgchat.so, libwmchat.so)
cmake --build "$ROOT/nchat/build"

# 4. launcher
mkdir -p "$HOME/.local/bin"
ln -sf "$ROOT/scripts/piazza" "$HOME/.local/bin/piazza"

# 5. config: preview script for Enter on an attachment, optional reset of old key/color defaults
set_conf() {
  mkdir -p "$(dirname "$1")"; touch "$1"
  if grep -q "^$2=" "$1"; then sed -i "s|^$2=.*|$2=$3|" "$1"; else echo "$2=$3" >> "$1"; fi
}
set_conf "$CONF/ui.conf" attachment_open_command "$ROOT/scripts/preview.sh '%1'"
if [ "$RESET" = 1 ]; then
  for f in key.conf color.conf; do
    [ -f "$CONF/$f" ] && mv "$CONF/$f" "$CONF/$f.bak"
  done
  echo "old key.conf / color.conf saved as *.bak, new defaults apply on next start"
fi

# 6. kitty mappings
if [ "$KITTY" = 1 ]; then
  KC="$HOME/.config/kitty/kitty.conf"
  mkdir -p "$(dirname "$KC")"; touch "$KC"
  if ! grep -q "piazza:" "$KC"; then
    printf '\n' >> "$KC"; cat "$ROOT/config/kitty.conf.snippet" >> "$KC"
    echo "kitty mappings added; reload with ctrl+shift+f5"
  fi
fi

echo
echo "done. Add accounts once with:  piazza -s     then run:  piazza"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) echo "note: add \$HOME/.local/bin to PATH" ;; esac
