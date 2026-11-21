# eFootball Prep

An adb script that sets up your eFootball tactics before a Division match: it reads the
opponent and sets your Individual Instructions to counter them.

It **never starts a match**. You press To Match yourself, before and after the script runs.

```
$ python3 efootball/efootball_prep.py
Waiting for the pre-match Game Plan…
  stadium screen → Next
Reading opponent…
  Long Ball Counter · ATK 4-3-3 / DEF 4-3-3 · strength 3168
Setting individual instructions…
  Defence2: DMF marks their SS 104
Done. Check the Game Plan, then press To Match yourself.
```

## Why

Individual Instructions reset for every Division match. Setting four of them by hand,
including finding the opponent's best playmaker for Man Marking, takes a few minutes of
tapping through menus. The script does it in about 90 seconds while you watch.

## Requirements

- An Android phone with **USB debugging** enabled and this computer authorised (`adb devices` shows `device`)
- `adb`
- Python 3 with Pillow (`pip install pillow`)
- Tesseract OCR with English data:
  - Arch: `sudo pacman -S tesseract tesseract-data-eng`
  - Debian/Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-eng`

## Usage

1. Open eFootball on the **Division** dashboard.
2. Press **To Match**.
3. Run:
   ```bash
   python3 efootball/efootball_prep.py
   ```
4. When it prints `Done`, check the Game Plan and press **To Match**.

You can start the script before matchmaking finishes. It waits up to 3 minutes for the
pre-match Game Plan to appear.

## What it does

1. **Waits** for the pre-match Game Plan. If the stadium/kit screen shows up first, it presses
   Next on it; that only moves to the Game Plan.
2. **Reads the opponent** from their team view: attacking and defensive formation,
   team playstyle and collective strength.
3. **Sets the Individual Instructions:**

   | Slot | Instruction | Our player | Why |
   |---|---|---|---|
   | Attack1 | Anchoring | DMF | Keeps a screen in front of the defence against counters |
   | Attack2 | Defensive | LB | Three defenders stay back while we attack |
   | Defence1 | Counter Target | SS (fast forward) | Stays high for the long ball when we win possession |
   | Defence2 | Man Marking | DMF | Marks their best creator: highest-rated AMF/SS, else CF, else winger, else CMF |

4. **Returns** to the pre-match Game Plan and stops.

## Configuration

The rules are constants at the top of `efootball/efootball_prep.py`. Edit them to match your squad:

```python
ANCHOR_POS = "DMF"          # Attack1 Anchoring
DEFENSIVE_POS = "LB"        # Attack2 Defensive
COUNTER_TARGET_POS = "SS"   # Defence1 Counter Target
MARKER_POS = "DMF"          # Defence2 Man Marking: who marks
CREATOR_TIERS = [("AMF", "SS"), ("CF",), ("LWF", "RWF", "LMF", "RMF"), ("CMF",)]
```

Players are found by the position label on their card, so the script follows
formation changes as long as each position above exists in your starting XI.

## How it works

- **Input:** eFootball ignores `adb shell input tap`, so every tap is a 120 ms press
  (`input swipe X Y X Y 120`).
- **Coordinates** are defined in a 1280-wide screenshot frame and scaled to the phone.
  They were mapped on a 2408×1080 screen. Other resolutions may need adjusting.
- **OCR:** card text is white and boosted ratings are yellow, on colourful player art.
  The script masks only bright pixels, thickens the strokes and runs Tesseract with tuned
  settings. On real screenshots it read 30/30 card positions and ratings, and 4/4 opponent
  formations, playstyles and strengths.
- **Screen detection** uses pixel probes (pitch green, gear tile, To Match button) plus OCR
  of the "General Settings" label on the stadium screen.

`efootball/NOTES.md` has the full screen map: every button coordinate, the post-match flow,
manager playstyle proficiencies, the strategy rules and a results log.

## Limitations

- Tuned for one device (vivo V2157, 2408×1080) and the game's UI as of November 2026.
  A UI update can move buttons.
- It doesn't change formation, manager or team playstyle; those stay as you set them.
- If something unexpected appears (event pop-up, network error), it exits instead of guessing.

## Fair play

This script only automates menu setup that you would otherwise do by hand. Starting matches
and playing them is left to you and the game. Automating gameplay or looping matches in
ranked online modes breaks Konami's terms and can get an account banned, so the script
doesn't do either. Use it at your own risk.
