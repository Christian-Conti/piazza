# Keys

| key | action |
| --- | --- |
| `Tab` / `Shift-Tab` | next / previous tab (service) |
| `F1`..`F9` | jump to tab N |
| `Ctrl-B` | next chat in tab |
| `←` / `→` | focus contacts / messages (with an empty prompt) |
| `Enter` on the contact list | open the conversation (same as `→`) |
| `Enter` on a message that quotes another | jump to the quoted message (a message with an attachment still opens the attachment) |
| `t` on a selected message, or `Alt-G` | Telegram forum **topics**: pick one to jump to its latest message; new messages are then sent to that topic. Each message shows its `#topic` in the header |
| `↑` `↓` | contacts (list focused) or messages |
| `←` then `↑` `↓` | **preview**: browse chats with the list focused; the right pane shows them but nothing is marked read until you open one (`→` or start typing) |
| `Esc` | leave message selection / quote, focus contacts |
| `Enter` | send; on a selected attachment: enlarge |
| `Shift-Enter` (`Alt-Enter`) | new line |
| `1`..`6` on a selected message | quick reaction 👍 ❤️ 😂 😮 😢 🙏 (same key again removes it) |
| `f` / `Alt-R` on a selected message | forward it: pick any chat of any service (type to filter), `Enter` sends |
| `r` / `Alt-S` on a selected message | full reaction list |
| `m` / `Ctrl-M` / `Alt-M` | on a selected message: quote it; again: drop quote |
| `Ctrl-V` / `Alt-V` | paste text or image |
| `Ctrl-T` | attach a file |
| `Alt-O` | open attachment (same as Enter on it) |
| `Space` / `Enter` on a voice message | play / pause it in the bubble; `PIAZZA_PLAYER` sets another player |
| tap / click | chat row, tab, bubble (selects it), quote card (jumps to the quoted message); wheel scrolls |
| `Alt-O` on audio | full-screen player (`space` pause, `q` stop) |
| `Ctrl-S` | emoji picker: `Tab`/`←`/`→` categories, `Enter` insert, recent first |
| `Ctrl-C` | clear prompt / cancel; on an empty prompt: quit |
| `Ctrl-Q` | quit |

Everything is configurable in `~/.config/nchat/key.conf`.
