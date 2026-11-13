#!/bin/sh
# Enlarge an attachment inside the terminal: pictures and short videos/GIFs via the kitty graphics protocol.
f="$1"
kitten="$(command -v kitten || echo "$HOME/.local/kitty.app/bin/kitten")"
mime="$(file -b --mime-type "$f")"
tmp=""
cleanup() { [ -n "$tmp" ] && rm -f "$tmp"; "$kitten" icat --clear 2>/dev/null; }
trap cleanup EXIT INT TERM

show() {
  clear
  "$kitten" icat --clear --align=center "$1"
  printf '\n  %s  -  Enter/q to close ' "$(basename "$f")"
  read -r _
}

case "$mime" in
  image/webp)
    # kitty cannot decode every WhatsApp webp; convert to PNG first
    if command -v ffmpeg >/dev/null 2>&1; then
      tmp="$(mktemp --suffix=.png)"
      ffmpeg -loglevel quiet -y -i "$f" -frames:v 1 "$tmp" </dev/null && show "$tmp" || show "$f"
    else
      show "$f"
    fi
    ;;
  image/*) show "$f" ;;
  video/*)
    dur="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null | cut -d. -f1)"
    if command -v ffmpeg >/dev/null 2>&1 && [ "${dur:-999}" -le 20 ]; then
      # short clip / GIF: play it looping in the terminal as an animated GIF
      tmp="$(mktemp --suffix=.gif)"
      ffmpeg -loglevel quiet -y -t 20 -i "$f" \
        -vf "fps=15,scale='min(640,iw)':-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
        "$tmp" </dev/null && show "$tmp" || xdg-open "$f" >/dev/null 2>&1 &
    else
      xdg-open "$f" >/dev/null 2>&1 &
    fi
    ;;
  *) xdg-open "$f" >/dev/null 2>&1 & ;;
esac
