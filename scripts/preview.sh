#!/bin/bash
# Open an attachment inside the terminal: pictures and short videos/GIFs via the kitty graphics protocol,
# audio (voice messages) with a playback bar; anything else with xdg-open.
#   audio keys: space = pause/resume, q / Enter / Esc = stop
#   PIAZZA_PLAYER overrides the audio player command (it is given the file as last argument)
f="$1"
kitten="$(command -v kitten || echo "$HOME/.local/kitty.app/bin/kitten")"
mime="$(file -b --mime-type "$f")"
tmp=""
apid=""
cleanup() {
  [ -n "$apid" ] && kill -CONT "$apid" 2>/dev/null && kill "$apid" 2>/dev/null
  [ -n "$tmp" ] && rm -f "$tmp"
  "$kitten" icat --clear 2>/dev/null
  tput cnorm 2>/dev/null
}
trap cleanup EXIT INT TERM

show() {
  clear
  "$kitten" icat --clear --align=center "$1"
  printf '\n  %s  -  any key to close%s ' "$(basename "$f")" "$2"
  local key=""
  IFS= read -rsn1 key
  if [ "$key" = "o" ] || [ "$key" = "O" ]; then
    xdg-open "$f" >/dev/null 2>&1 &
  fi
  return 0
}

fmt_time() { printf '%d:%02d' $(($1 / 60)) $(($1 % 60)); }

play_audio() {
  local dur
  dur="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null | cut -d. -f1)"
  dur="${dur:-0}"
  if [ -n "${PIAZZA_PLAYER:-}" ]; then
    eval "$PIAZZA_PLAYER \"\$f\"" >/dev/null 2>&1 &
  elif command -v ffplay >/dev/null 2>&1; then
    ffplay -nodisp -autoexit -loglevel quiet "$f" >/dev/null 2>&1 &
  elif command -v pw-play >/dev/null 2>&1; then
    pw-play "$f" >/dev/null 2>&1 &
  elif command -v paplay >/dev/null 2>&1; then
    paplay "$f" >/dev/null 2>&1 &
  else
    xdg-open "$f" >/dev/null 2>&1 &
    return
  fi
  apid=$!

  clear
  printf '\n  \033[1m\xe2\x99\xaa  %s\033[0m\n\n' "$(basename "$f")"
  tput civis 2>/dev/null
  local paused=0 start now elapsed pausedAt=0 pausedTotal=0 key cols barw filled i bar pct
  start="$(date +%s%N)"
  while kill -0 "$apid" 2>/dev/null; do
    now="$(date +%s%N)"
    if [ "$paused" = 1 ]; then now="$pausedAt"; fi
    elapsed=$(( (now - start - pausedTotal) / 1000000000 ))
    cols="$(tput cols 2>/dev/null || echo 80)"
    barw=$((cols - 34)); [ "$barw" -lt 8 ] && barw=8
    if [ "$dur" -gt 0 ]; then
      [ "$elapsed" -gt "$dur" ] && elapsed="$dur"
      filled=$((elapsed * barw / dur))
    else
      filled=$((elapsed % (barw + 1)))
    fi
    bar=""
    for ((i = 0; i < barw; i++)); do
      if [ "$i" -lt "$filled" ]; then bar="$bar\xe2\x96\x88"; else bar="$bar\xe2\x96\x91"; fi
    done
    icon="\xe2\x96\xb6"; [ "$paused" = 1 ] && icon="\xe2\x8f\xb8"
    if [ "$dur" -gt 0 ]; then pct=" $((elapsed * 100 / dur))%"; else pct=""; fi
    printf "\r  $icon %s  $bar  %s%s\033[K" "$(fmt_time "$elapsed")" "$( [ "$dur" -gt 0 ] && fmt_time "$dur" || echo '--:--')" "$pct"
    key=""
    if IFS= read -rsn1 -t 0.15 key; then
      case "$key" in
        " ")
          if [ "$paused" = 0 ]; then
            kill -STOP "$apid" 2>/dev/null; paused=1; pausedAt="$(date +%s%N)"
          else
            kill -CONT "$apid" 2>/dev/null; paused=0; pausedTotal=$((pausedTotal + $(date +%s%N) - pausedAt))
          fi ;;
        q|""|$'\e') kill -CONT "$apid" 2>/dev/null; kill "$apid" 2>/dev/null; break ;;
      esac
    fi
  done
  printf '\n\n  space: pause   q / Enter: close\r'
  apid=""
}

case "$mime" in
  audio/*|application/ogg|video/ogg) play_audio ;;
  image/webp)
    # kitty cannot decode every WhatsApp webp; convert to PNG first
    if command -v ffmpeg >/dev/null 2>&1; then
      tmp="$(mktemp --suffix=.png)"
      if ffmpeg -loglevel quiet -y -i "$f" -frames:v 1 "$tmp" </dev/null; then show "$tmp" ""; else show "$f" ""; fi
    else
      show "$f" ""
    fi
    ;;
  image/*) show "$f" "" ;;
  video/*)
    if command -v ffmpeg >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
      # built-in player: frames streamed to kitty, sound through ffplay, starts immediately
      # foreground: a trailing & would background the whole "a || b" list and the player would lose the keyboard
      if ! python3 "$(dirname "$(readlink -f "$0")")/vplay.py" "$f" 2>/tmp/piazza-vplay.err; then
        xdg-open "$f" >/dev/null 2>&1 &
      fi
    else
      xdg-open "$f" >/dev/null 2>&1 &
    fi
    ;;
  *) xdg-open "$f" >/dev/null 2>&1 & ;;
esac
