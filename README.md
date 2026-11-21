# Phone Deck

Small tools for controlling an Android phone (vivo V2157, Android 14) from this laptop over USB debugging.
Everything runs on plain `adb`; nothing is installed on the phone.

## Requirements

- `adb` with the phone connected and USB debugging authorised (`adb devices` shows `device`)
- Python 3 with Pillow
- For eFootball prep only: `tesseract` with English data (`sudo pacman -S tesseract-data-eng`)

## What's here

| Path | What it does |
|---|---|
| `server.py` + `index.html` | **Phone Deck**: a web dashboard with a live screen mirror, tap/swipe/type control and battery/RAM/storage stats |
| `restore-bloatware.sh` | Re-enables the vivo apps that were disabled on 2026-11-21 |
| `efootball/efootball_prep.py` | Sets up eFootball match tactics automatically before a Division match |
| `efootball/NOTES.md` | eFootball screen map, manager proficiencies, strategy rules and results log |

## Phone Deck

```bash
python3 ~/phone-deck/server.py
```

Open http://127.0.0.1:8765.

- **Screen:** refreshes about once a second. Click it to tap the phone, drag on it to swipe.
- **Buttons:** Back, Home, Recents, Wake, Power, Volume ±, Play/Pause.
- **Text box:** types into whatever field is focused on the phone.
- **Stats:** battery and charging, temperature, RAM, storage, uptime, screen state and the foreground app.

The server listens on `127.0.0.1` only, so other devices on the network can't reach it.
For smooth video with sound, use `scrcpy` instead.

## eFootball prep

Prepares tactics for a Division match. It **never starts a match**; you press To Match yourself.

1. Open eFootball on the Division dashboard and press **To Match**.
2. Run:
   ```bash
   python3 ~/phone-deck/efootball/efootball_prep.py
   ```
3. When it prints `Done`, check the Game Plan and press **To Match**.

The script:

1. waits for matchmaking and skips the stadium screen
2. reads the opponent's formation, playstyle and strength
3. sets all four Individual Instructions:
   - Anchoring → DMF
   - Defensive → LB
   - Counter Target → SS (Mbappé)
   - Man Marking: our DMF on their best AMF/SS
4. stops on the pre-match Game Plan

It takes about 90 seconds.

To change who gets each instruction, edit the constants at the top of `efootball_prep.py`
(`ANCHOR_POS`, `DEFENSIVE_POS`, `COUNTER_TARGET_POS`, `MARKER_POS`, `CREATOR_TIERS`).
See `efootball/NOTES.md` for every button's coordinates and the reasoning behind the rules.

> Full match automation (auto-pressing To Match in a loop) was deliberately left out.
> Division is ranked online play, and botting it risks a Konami account ban.

## Changes made to the phone on 2026-11-21

| Change | How to undo |
|---|---|
| Animation scales set to 0.5x | Developer options → the three animation scales → 1x |
| 11 vivo/Facebook preinstalled apps disabled (not uninstalled) | `~/phone-deck/restore-bloatware.sh` |
| Naruto Storm 3 folder deleted (7 GB) and app caches cleared | Not reversible (the folder held old PS3 game files) |

## Gotchas

- **eFootball ignores `adb shell input tap`.** Use a short press instead: `input swipe X Y X Y 120`.
- Coordinates in the eFootball notes use a 1280-wide screenshot frame. Multiply by 2408/1280 for real taps.
- Some phone settings are locked by vivo. V-Appstore, Jovi (hiboard) and vivo website can't be disabled without root.
