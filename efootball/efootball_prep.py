#!/usr/bin/env python3
"""eFootball match prep over adb.

Run it while the phone shows the PRE-MATCH Game Plan (the pitch screen that
appears after you press "To Match" and an opponent is found). It will:

  1. open the opponent's team and read their formation, playstyle and strength
  2. open Individual Instructions and set all four from the rules below
  3. return to the pre-match Game Plan and stop

It never presses "To Match" — you start the match yourself.
Layout and rules are documented in NOTES.md next to this file.

Requires: adb, python3-pillow, tesseract + English data
(Arch: sudo pacman -S tesseract-data-eng).
"""
import argparse
import difflib
import io
import re
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageChops, ImageFilter, ImageOps

PHONE_W = 2408          # landscape width of the vivo V2157
FRAME_W = 1280          # all coordinates below are in a 1280-wide screenshot
SCALE = PHONE_W / FRAME_W

# ---- our side of the rules (edit when the squad changes) -------------------
ANCHOR_POS = "DMF"          # Attack1 Anchoring
DEFENSIVE_POS = "LB"        # Attack2 Defensive
COUNTER_TARGET_POS = "SS"   # Defence1 Counter Target (Mbappé plays SS on the left)
MARKER_POS = "DMF"          # Defence2 Man Marking: who marks

# Opponent target for Man Marking, best first. Highest rating wins within a tier.
CREATOR_TIERS = [("AMF", "SS"), ("CF",), ("LWF", "RWF", "LMF", "RMF"), ("CMF",)]

PLAYSTYLES = ["Possession Game", "Quick Counter", "Long Ball Counter", "Out Wide", "Long Ball", "Overload"]

# ---- screen coordinates (1280 frame) ---------------------------------------
BACK = (225, 522)
NEXT = (1055, 522)
GEAR = (165, 435)
OPPONENT_TEAM = (380, 435)
SWITCH_ATK_DEF = (1113, 342)
MANAGER = (165, 110)
INDIVIDUAL_INSTR_PREMATCH = (808, 404)
CARDS = {"Attack1": (340, 260), "Attack2": (640, 260), "Defence1": (937, 260), "Defence2": (1180, 260)}
ATTACK_OPT = {"Off": (600, 150), "Defensive": (600, 211), "Anchoring": (600, 271)}
DEFENCE_OPT = {"Off": (600, 150), "Tight Marking": (600, 211), "Man Marking": (600, 271),
               "Counter Target": (600, 331)}
PICKER_COLS = (666, 783, 900, 1017)
PICKER_ROWS = (186, 300, 420)
PICKER_DONE = (1034, 90)
PICKER_NEXT = (1022, 90)


def adb(*args, binary=False):
    out = subprocess.run(["adb", *args], capture_output=True, timeout=20)
    return out.stdout if binary else out.stdout.decode(errors="replace")


def shot():
    img = Image.open(io.BytesIO(adb("exec-out", "screencap", "-p", binary=True))).convert("RGB")
    return img.resize((FRAME_W, round(img.height * FRAME_W / img.width)))


def tap(xy, wait=1.8):
    # The game ignores `input tap`; a 120 ms press registers.
    x, y = (round(v * SCALE) for v in xy)
    adb("shell", "input", "swipe", str(x), str(y), str(x), str(y), "120")
    time.sleep(wait)


def text_mask(img, floor=185, yellow=False, thicken=0):
    """Black-on-white mask of the card text. Labels are white; boosted ratings are
    yellow, so for digits only red and green need to be bright."""
    img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
    r, g, b = img.split()
    bright = ImageChops.darker(r, g) if yellow else ImageChops.darker(ImageChops.darker(r, g), b)
    mask = bright.point(lambda v: 0 if v > floor else 255)
    if thicken:
        # Thicker strokes bridge the cuts in the stencil font and anti-aliased edges
        mask = mask.filter(ImageFilter.MinFilter(thicken))
    return ImageOps.expand(mask, border=12, fill=255)


def ocr(img, whitelist=None, psm=7, **mask_opts):
    img = text_mask(img, **mask_opts)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    cmd = ["tesseract", "-", "-", "--psm", str(psm), "-l", "eng"]
    if whitelist:
        cmd += ["-c", f"tessedit_char_whitelist={whitelist}"]
    return subprocess.run(cmd, input=buf.getvalue(), capture_output=True).stdout.decode().strip()


def read_card(img, cx, cy):
    """Position label and rating from a player card centred at (cx, cy)."""
    pos = ocr(img.crop((cx - 42, cy - 34, cx - 2, cy - 16)), "ABCDFGKLMRSW")
    # floor/thicken/psm picked by grid search: 30/30 ratings correct on saved pickers
    rating = ocr(img.crop((cx - 44, cy - 18, cx + 4, cy + 6)), "0123456789", psm=13,
                 yellow=True, floor=215, thicken=3)
    m = re.search(r"\d{2,3}", rating)
    value = int(m.group()) if m else 0
    # Bright player art behind the digits sometimes produces junk like 929 or 10
    return pos, value if 40 <= value <= 115 else 0


def read_picker(img):
    cards = []
    for cy in PICKER_ROWS:
        for cx in PICKER_COLS:
            # Empty grid slots are pure white; some cards are bright, so use a strict cut-off
            if sum(img.getpixel((cx, cy))) > 760:
                continue
            pos, rating = read_card(img, cx, cy)
            if pos:
                cards.append({"pos": pos, "rating": rating, "xy": (cx, cy)})
    return cards


def find(cards, pos):
    hits = [c for c in cards if c["pos"] == pos]
    if not hits:
        sys.exit(f"Could not find a {pos} in the picker: {[c['pos'] for c in cards]}")
    return max(hits, key=lambda c: c["rating"])


def pick_creator(cards):
    for tier in CREATOR_TIERS:
        hits = [c for c in cards if c["pos"] in tier]
        if hits:
            return max(hits, key=lambda c: c["rating"])
    return max(cards, key=lambda c: c["rating"])


def is_prematch(img):
    """Pre-match Game Plan: pitch in the middle, gear tile bottom-left, To Match bottom-right.
    The Division Game Plan has a blue jersey where the gear is and no To Match button."""
    r, g, b = img.getpixel((640, 350))
    return g > r and g > b and sum(img.getpixel((165, 435))) > 700 and sum(img.getpixel((1055, 522))) > 700


def is_stadium(img):
    """Kit/stadium screen shown before the pre-match Game Plan. Its Next only advances
    to the Game Plan; it does not start the match."""
    return "General" in ocr(img.crop((540, 445, 745, 488)))


def wait_for_prematch(timeout=180):
    deadline = time.time() + timeout
    while time.time() < deadline:
        img = shot()
        if is_prematch(img):
            return
        if is_stadium(img):
            print("  stadium screen → Next")
            tap(NEXT, 4)
            continue
        time.sleep(3)
    sys.exit("Pre-match Game Plan did not appear. Press To Match on the Division dashboard first.")


def read_opponent():
    tap(GEAR, 1.2)
    tap(OPPONENT_TEAM, 2.5)
    info = {}
    for phase in ("attack", "defence"):
        img = shot()
        info[phase] = ocr(img.crop((325, 8, 420, 40)), "0123456789-")
        if phase == "attack":
            # A forward's card can cover the first letters, so snap to the closest known style
            raw = re.sub(r"[^A-Za-z ]", "", ocr(img.crop((760, 8, 960, 40)))).strip()
            info["style"] = (difflib.get_close_matches(raw, PLAYSTYLES, n=1, cutoff=0.5) or [raw])[0]
            info["strength"] = ocr(img.crop((1035, 120, 1190, 182)), "0123456789", yellow=True, thicken=7)
            tap(SWITCH_ATK_DEF, 1.5)
    tap(BACK, 2)
    return info


def set_instruction(card, option, our_pos=None, their_pick=None):
    tap(CARDS[card], 1.8)
    tap(option, 1.8)
    if our_pos:
        ours = find(read_picker(shot()), our_pos)
        tap(ours["xy"], 1.0)
    if their_pick:
        tap(PICKER_NEXT, 1.8)
        target = their_pick(read_picker(shot()))
        tap(target["xy"], 1.0)
        print(f"  {card}: {our_pos} marks their {target['pos']} {target['rating']}")
    tap(PICKER_DONE, 1.8)
    tap(BACK, 1.8)


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    if not shutil.which("tesseract"):
        sys.exit("tesseract not found")
    if "eng" not in subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout:
        sys.exit("Tesseract English data missing: sudo pacman -S tesseract-data-eng")

    print("Waiting for the pre-match Game Plan…")
    wait_for_prematch()
    print("Reading opponent…")
    opp = read_opponent()
    print(f"  {opp['style']} · ATK {opp['attack']} / DEF {opp['defence']} · strength {opp['strength']}")

    print("Setting individual instructions…")
    tap(MANAGER, 1.8)
    tap(INDIVIDUAL_INSTR_PREMATCH, 2.5)
    set_instruction("Attack1", ATTACK_OPT["Anchoring"], ANCHOR_POS)
    set_instruction("Attack2", ATTACK_OPT["Defensive"], DEFENSIVE_POS)
    set_instruction("Defence1", DEFENCE_OPT["Counter Target"], COUNTER_TARGET_POS)
    set_instruction("Defence2", DEFENCE_OPT["Man Marking"], MARKER_POS, their_pick=pick_creator)
    tap(BACK, 2)

    if opp["attack"].count("-") >= 2 and opp["attack"].startswith("3"):
        print("Note: they attack with three at the back — Long Ball Counter should feast.")
    print("Done. Check the Game Plan, then press To Match yourself.")


if __name__ == "__main__":
    main()
