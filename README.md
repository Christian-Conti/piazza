# piazza

All your chats in one terminal, one tab per service. A patched [nchat](https://github.com/d99kris/nchat)
(kept as an untouched git submodule + a patch), built for kitty.

- **Tabs per service** (WhatsApp, Telegram, Signal, ... whatever nchat has an account for), colored per service,
  with unread counts. Adding another account adds another tab, no code change.
- **Messaging-app layout**: full-height contact column, chat title, rounded colored bubbles (sent on the right).
- **Inline images, stickers, GIFs, videos** via the kitty graphics protocol; a media-only bubble shrinks to the picture size (no file name), videos show a thumbnail with a `▶ 0:12` badge; `Enter` enlarges, short videos/GIFs loop in the terminal.
- **Voice messages / audio** play inside the bubble (`▶ ━━●──── 0:12/0:31`): select the message, `Space` or `Enter` plays/pauses. `Alt-O` opens the full-screen player.
- **Reactions**: select a message, `1`..`6` give 👍 ❤️ 😂 😮 😢 🙏 (again = remove), `r` opens the full list.
- **Touch / mouse**: tap a chat, a tab or a bubble to open/select it; tap a quote card to jump to the message it quotes; the wheel scrolls (hold Shift to select text, `mouse_enabled=0` in `ui.conf` turns it off).
- **Forward** a selected message to any chat of any service with `f` (type to filter the chat list); attachments must be downloaded first.
- **Replies**: `m` / `Ctrl+M` on a selected message quotes it, quotes show as an inset card.
- **Paste images** (`Ctrl+V`), **attach files** (`Ctrl+T`, with an upload spinner / progress bar), emoji picker with *recent* and categories, sound on new messages.
- Truly round bubble corners in kitty (antialiased corner images in the exact color of your theme; block-character corners elsewhere), rounded dialogs, date separators, last-activity times in the contact list, prompt with hint, muted metadata.
- Colors come from your terminal theme. Sent bubbles use the service color, received ones the same hue muted toward your terminal background (`muted0`..`muted5` in `color.conf`), so the two are clearly distinguishable. WhatsApp green, Telegram blue, Signal cyan.

## Install

```sh
git clone --recurse-submodules <this repo> piazza && cd piazza
./install.sh --kitty          # build, install `piazza` launcher, kitty key mappings
piazza -s                     # add accounts (WhatsApp QR, Telegram code)
piazza
```

Needs: `git cmake ninja go gperf patch` + a C++ toolchain and the libs listed by `install.sh`.
Optional: `ffmpeg` (GIF/video/webp thumbnails), `pw-play` or `paplay` (sound), kitty (inline images).
Config stays in `~/.config/nchat`. Existing `key.conf` / `color.conf` keep old values: run `./install.sh --reset-config` to take the new defaults.

## Layout

| path | what |
| --- | --- |
| `nchat/` | upstream nchat, git submodule pinned to a commit, patched in place by `install.sh` |
| `patches/0001-piazza.patch` | all changes to nchat |
| `scripts/preview.sh` | full-screen preview for images, webp, short videos/GIFs |
| `scripts/piazza` | launcher |
| `config/kitty.conf.snippet` | Shift+Enter / Ctrl+M mappings |

See [docs/KEYS.md](docs/KEYS.md) for keys.

## License

MIT, see [LICENSE](LICENSE). piazza is a set of patches on top of [nchat](https://github.com/d99kris/nchat) (MIT), which fixes the floor: derived code cannot be licensed more freely than MIT. The libraries nchat pulls in keep their own licenses (Signal support is AGPL, WhatsApp MPL, TDLib Boost); piazza patches none of those.

## Updating the patch after changing nchat sources

```sh
scripts/update-patch.sh
```

`./uninstall.sh` removes the launcher again.
